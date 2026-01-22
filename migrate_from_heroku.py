#!/usr/bin/env python3
"""
Database migration script to run on Render.
Migrates data from Heroku Postgres to Render Postgres using internal connection.
This script uses psycopg to copy data table by table, avoiding version issues.
"""
import json
import os
import sys

# Try to import psycopg, install if needed
try:
    import psycopg
    from psycopg import sql
    from psycopg.types.json import Jsonb
except ImportError:
    print("Installing psycopg...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg[binary]'])
    import psycopg
    from psycopg import sql
    from psycopg.types.json import Jsonb

def get_all_tables(conn):
    """Get list of all tables in the database."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
            ORDER BY table_name;
        """)
        return [row[0] for row in cur.fetchall()]

def _json_dumps_default(obj):
    """JSON serializer for Wagtail revision content (handles datetime, Decimal, etc.)."""
    from decimal import Decimal
    from datetime import date, datetime, time
    if isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def copy_table_data(source_conn, dest_conn, table_name, skip_columns=None, json_columns=None, filter_null_columns=None, fk_fix_columns=None):
    """Copy data from source to destination table.
    
    Args:
        fk_fix_columns: List of tuples (column_name, referenced_table) to fix FK references.
                       If referenced record doesn't exist, set to NULL.
    """
    print(f"  Copying {table_name}...", end=' ', flush=True)
    json_columns = json_columns or []
    filter_null_columns = filter_null_columns or []
    fk_fix_columns = fk_fix_columns or []
    
    try:
        # Check if table exists in destination
        with dest_conn.cursor() as check_cur:
            check_cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = %s
                );
            """, (table_name,))
            if not check_cur.fetchone()[0]:
                print("(table doesn't exist, skipping)")
                return 0
        
        # Get column info from destination (to match schema)
        with dest_conn.cursor() as dest_cur:
            dest_cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            dest_columns = [row[0] for row in dest_cur.fetchall()]
        
        # Filter out columns that don't exist in destination
        if skip_columns:
            dest_columns = [col for col in dest_columns if col not in skip_columns]
        
        if not dest_columns:
            print("(no matching columns, skipping)")
            return 0
        
        # Get data from source (only columns that exist in destination)
        with source_conn.cursor() as src_cur:
            # Check which columns exist in source
            src_cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = %s
            """, (table_name,))
            source_columns = [row[0] for row in src_cur.fetchall()]
            
            # Only select columns that exist in both
            common_columns = [col for col in dest_columns if col in source_columns]
            
            if not common_columns:
                print("(no common columns, skipping)")
                return 0
            
            cols_sql = sql.SQL(', ').join(map(sql.Identifier, common_columns))
            src_cur.execute(sql.SQL("SELECT {} FROM {}").format(cols_sql, sql.Identifier(table_name)))
            rows = src_cur.fetchall()
        
        if not rows:
            print("(empty)")
            return 0
        
        # Filter out rows with NULL values in required columns
        if filter_null_columns:
            filter_indices = {i for i, c in enumerate(common_columns) if c in filter_null_columns}
            if filter_indices:
                original_count = len(rows)
                rows = [row for row in rows if all(row[i] is not None for i in filter_indices)]
                filtered_count = original_count - len(rows)
                if filtered_count > 0:
                    print(f"(filtered {filtered_count} rows with NULL in required columns) ", end='', flush=True)
        
        if not rows:
            print("(empty after filtering)")
            return 0
        
        # Get valid foreign key IDs if we need to fix FK references
        valid_fk_ids_map = {}
        if fk_fix_columns:
            for col_name, ref_table in fk_fix_columns:
                if col_name in common_columns:
                    col_idx = common_columns.index(col_name)
                    try:
                        with dest_conn.cursor() as fk_cur:
                            fk_cur.execute(sql.SQL("SELECT id FROM {}").format(sql.Identifier(ref_table)))
                            valid_ids = {row[0] for row in fk_cur.fetchall()}
                            valid_fk_ids_map[col_idx] = (col_name, valid_ids)
                            print(f"(checking {col_name} refs to {ref_table}: {len(valid_ids)} valid) ", end='', flush=True)
                    except Exception as e:
                        print(f"(warning: could not check {col_name} refs: {e}) ", end='', flush=True)
        
        # Transform rows: wrap json_columns values in Jsonb for psycopg
        # Also handle foreign key references that might not exist
        json_indices = {i for i, c in enumerate(common_columns) if c in json_columns}
        
        def adapt_row(row):
            r = list(row)
            
            # Fix foreign key references to non-existent records
            for col_idx, (col_name, valid_ids) in valid_fk_ids_map.items():
                if r[col_idx] is not None and r[col_idx] not in valid_ids:
                    # Set to NULL if referenced record doesn't exist
                    r[col_idx] = None
            
            # Handle JSON columns
            if json_indices:
                for i in json_indices:
                    v = r[i]
                    if v is not None:
                        # If already a dict/list, wrap in Jsonb with custom dumps for datetime/Decimal
                        if isinstance(v, (dict, list)):
                            r[i] = Jsonb(v, dumps=lambda o: json.dumps(o, default=_json_dumps_default))
                        # If it's a string, try to parse as JSON first (unlikely from psycopg, but handle it)
                        elif isinstance(v, str):
                            try:
                                parsed = json.loads(v)
                                r[i] = Jsonb(parsed, dumps=lambda o: json.dumps(o, default=_json_dumps_default))
                            except (TypeError, ValueError):
                                # Not valid JSON string - pass through (will likely fail, but be explicit)
                                r[i] = v
                        # For other types (None, int, etc.), pass through as-is
                        # None will fail if column is NOT NULL, which is expected
            return tuple(r)
        
        rows = [adapt_row(r) for r in rows]
        
        # Insert into destination - try batch insert, fall back to row-by-row on error
        with dest_conn.cursor() as dest_cur:
            # Build INSERT statement - use ON CONFLICT only if we have an 'id' column (primary key)
            cols = sql.SQL(', ').join(map(sql.Identifier, common_columns))
            placeholders = sql.SQL(', ').join(sql.Placeholder() * len(common_columns))
            
            # Check if 'id' is in the columns (primary key)
            # For critical Wagtail tables, use UPDATE on conflict to overwrite existing data
            # For other tables, use DO NOTHING to skip duplicates
            if 'id' in common_columns:
                if table_name in ['wagtailcore_page', 'wagtailcore_site', 'wagtailcore_revision']:
                    # For critical tables, update on conflict (but only if we have all columns)
                    # Build UPDATE clause for all non-id columns
                    update_cols = [col for col in common_columns if col != 'id']
                    if update_cols:
                        update_set = sql.SQL(', ').join(
                            sql.SQL("{} = EXCLUDED.{}").format(sql.Identifier(col), sql.Identifier(col))
                            for col in update_cols
                        )
                        insert_query = sql.SQL("""
                            INSERT INTO {} ({}) VALUES ({}) 
                            ON CONFLICT (id) DO UPDATE SET {}
                        """).format(
                            sql.Identifier(table_name),
                            cols,
                            placeholders,
                            update_set
                        )
                    else:
                        # Fallback to DO NOTHING if no columns to update
                        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT (id) DO NOTHING").format(
                            sql.Identifier(table_name),
                            cols,
                            placeholders
                        )
                else:
                    # For other tables, skip duplicates
                    insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT (id) DO NOTHING").format(
                        sql.Identifier(table_name),
                        cols,
                        placeholders
                    )
            else:
                # No primary key conflict handling - just insert (will fail on duplicates)
                insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),
                    cols,
                    placeholders
                )
            
            try:
                dest_cur.executemany(insert_query, rows)
                rows_inserted = dest_cur.rowcount
                dest_conn.commit()
                print(f"✓ ({rows_inserted} rows inserted/updated)")
                return rows_inserted if rows_inserted > 0 else len(rows)
            except Exception as batch_error:
                # If batch insert fails, try row-by-row to identify problematic rows
                dest_conn.rollback()
                error_msg = str(batch_error)
                print(f"\n    Batch error: {error_msg[:200]}", end='', flush=True)
                print(f"\n    Trying row-by-row insertion... ", end='', flush=True)
                successful = 0
                failed = 0
                error_samples = []
                for idx, row in enumerate(rows):
                    try:
                        dest_cur.execute(insert_query, row)
                        successful += 1
                    except Exception as row_error:
                        failed += 1
                        # Collect first few errors for reporting
                        if len(error_samples) < 3:
                            error_samples.append((idx, str(row_error)[:150]))
                dest_conn.commit()
                if successful > 0:
                    print(f"✓ ({successful} rows succeeded, {failed} failed)")
                    if error_samples:
                        print(f"    Sample errors:")
                        for idx, err in error_samples:
                            print(f"      Row {idx}: {err}")
                    return successful
                else:
                    # All rows failed - show the batch error
                    raise batch_error  # Re-raise if all rows failed
    except Exception as e:
        error_msg = str(e)
        print(f"✗ Error: {error_msg[:200]}")
        dest_conn.rollback()
        return 0

def main():
    print("=" * 60)
    print("Database Migration: Heroku Postgres → Render Postgres")
    print("=" * 60)
    
    # Get connection strings from environment
    HEROKU_DATABASE_URL = os.environ.get('HEROKU_DATABASE_URL')
    RENDER_DATABASE_URL = os.environ.get('DATABASE_URL')  # Render sets this automatically when linked
    
    if not HEROKU_DATABASE_URL:
        print("⚠ HEROKU_DATABASE_URL not set. Skipping migration.")
        print("To migrate: Set HEROKU_DATABASE_URL in Render dashboard → Environment")
        return 0
    
    if not RENDER_DATABASE_URL:
        print("⚠ DATABASE_URL not set. Database may not be linked to service.")
        print("Link the database in Render dashboard first.")
        return 0
    
    print(f"\nSource: Heroku Postgres")
    print(f"Destination: Render Postgres (internal)")
    
    # Connect to databases
    print("\nStep 1: Connecting to databases...")
    try:
        source_conn = psycopg.connect(HEROKU_DATABASE_URL)
        print("✓ Connected to Heroku Postgres")
    except Exception as e:
        print(f"✗ Failed to connect to Heroku: {e}")
        return 1
    
    try:
        dest_conn = psycopg.connect(RENDER_DATABASE_URL)
        print("✓ Connected to Render Postgres")
    except Exception as e:
        print(f"✗ Failed to connect to Render: {e}")
        source_conn.close()
        return 1
    
    # Get list of tables
    print("\nStep 2: Discovering tables...")
    try:
        tables = get_all_tables(source_conn)
        print(f"✓ Found {len(tables)} tables")
    except Exception as e:
        print(f"✗ Error getting tables: {e}")
        source_conn.close()
        dest_conn.close()
        return 1
    
    # Copy data
    # Strategy: Copy Wagtail core tables first (in order), then other tables
    print("\nStep 3: Copying data...")
    print("Note: Django system tables are skipped (created by migrations)")
    
    # Tables to skip
    skip_tables = {
        'django_migrations',
        'django_content_type',
        'django_admin_log',
        'django_session',
        'auth_permission',
        'auth_group',
        'auth_group_permissions',
    }
    
    # Wagtail tables to copy in order (respecting foreign key dependencies)
    wagtail_tables_order = [
        'wagtailcore_locale',
        'wagtailcore_collection',
        'wagtailcore_revision',  # Copy revisions first (pages reference them)
        'wagtailcore_page',  # Copy pages (sites reference them)
        'wagtailcore_site',  # Copy sites last (they reference pages)
        'wagtailimages_image',
        'wagtailimages_rendition',
        'wagtaildocs_document',
    ]
    
    # Other Wagtail tables (can be copied in any order)
    wagtail_prefixes = ['wagtailcore_', 'wagtailimages_', 'wagtaildocs_', 'wagtailforms_', 
                        'wagtailredirects_', 'wagtailsearch_', 'wagtailusers_', 'wagtailadmin_']
    
    total_rows = 0
    skipped = 0
    
    # First, copy Wagtail core tables in order
    print("\nCopying Wagtail core tables (in dependency order)...")
    
    for table in wagtail_tables_order:
        if table in tables:
            # For wagtailcore_revision, handle JSON content column properly and filter NULL content_type_id
            skip_cols = None
            json_cols = None
            filter_null_cols = None
            fk_fix_cols = None
            
            if table == 'wagtailcore_revision':
                json_cols = ['content']  # Wrap content in Jsonb for proper JSON serialization
                filter_null_cols = ['content_type_id']  # Filter out rows with NULL content_type_id (NOT NULL constraint)
            
            elif table == 'wagtailcore_page':
                # Fix foreign key references that might not exist
                fk_fix_cols = [
                    ('live_revision_id', 'wagtailcore_revision'),
                    ('latest_revision_id', 'wagtailcore_revision'),
                    ('locale_id', 'wagtailcore_locale'),  # Pages reference locales
                ]
                # Note: owner_id FK to auth_user is handled separately (auth_user is copied)
                # Note: content_type_id FK to django_content_type is created by migrations
            
            elif table == 'wagtailcore_site':
                # Fix foreign key reference to root_page_id - pages must exist first
                fk_fix_cols = [
                    ('root_page_id', 'wagtailcore_page'),
                ]
            
            rows = copy_table_data(
                source_conn, dest_conn, table, 
                skip_columns=skip_cols, 
                json_columns=json_cols, 
                filter_null_columns=filter_null_cols,
                fk_fix_columns=fk_fix_cols
            )
            total_rows += rows
    
    # Then copy other Wagtail tables
    print("\nCopying other Wagtail tables...")
    for table in tables:
        if table in wagtail_tables_order:
            continue  # Already copied
        if any(table.startswith(prefix) for prefix in wagtail_prefixes):
            rows = copy_table_data(source_conn, dest_conn, table)
            total_rows += rows
    
    # Finally, copy non-Wagtail tables
    print("\nCopying other tables...")
    for table in tables:
        # Skip Django system tables
        if table in skip_tables or (table.startswith('django_') and table not in ['django_site']):
            print(f"  Skipping {table} (Django system table)")
            skipped += 1
            continue
        
        # Skip if already copied
        if any(table.startswith(prefix) for prefix in wagtail_prefixes):
            continue
        
        rows = copy_table_data(source_conn, dest_conn, table)
        total_rows += rows
    
    # Verify critical tables were copied
    print("\n" + "=" * 60)
    print("Verifying migration results...")
    print("=" * 60)
    
    verification_passed = True
    with dest_conn.cursor() as verify_cur:
        # Check revisions
        verify_cur.execute("SELECT COUNT(*) FROM wagtailcore_revision")
        rev_count = verify_cur.fetchone()[0]
        print(f"  wagtailcore_revision: {rev_count} rows")
        if rev_count == 0:
            print("    ⚠ WARNING: No revisions copied!")
            verification_passed = False
        
        # Check pages
        verify_cur.execute("SELECT COUNT(*) FROM wagtailcore_page")
        page_count = verify_cur.fetchone()[0]
        print(f"  wagtailcore_page: {page_count} rows")
        if page_count <= 1:  # 1 is just the root page created by migrations
            print("    ⚠ WARNING: No content pages copied! (only root page exists)")
            verification_passed = False
        else:
            # Check for HomePage specifically
            verify_cur.execute("""
                SELECT COUNT(*) FROM wagtailcore_page p
                JOIN django_content_type ct ON p.content_type_id = ct.id
                WHERE ct.app_label = 'lampstands' AND ct.model = 'homepage'
            """)
            homepage_count = verify_cur.fetchone()[0]
            print(f"    HomePage instances: {homepage_count}")
            if homepage_count == 0:
                print("    ⚠ WARNING: No HomePage found!")
                verification_passed = False
            else:
                # Show HomePage details
                verify_cur.execute("""
                    SELECT p.id, p.title, p.live, p.depth, p.path
                    FROM wagtailcore_page p
                    JOIN django_content_type ct ON p.content_type_id = ct.id
                    WHERE ct.app_label = 'lampstands' AND ct.model = 'homepage'
                    ORDER BY p.depth, p.path
                    LIMIT 5
                """)
                homepages = verify_cur.fetchall()
                print(f"    HomePage details:")
                for hp_id, title, live, depth, path in homepages:
                    print(f"      - {title} (ID: {hp_id}, live: {live}, depth: {depth}, path: {path})")
            
            # Show page type breakdown
            verify_cur.execute("""
                SELECT ct.app_label, ct.model, COUNT(*) as count
                FROM wagtailcore_page p
                JOIN django_content_type ct ON p.content_type_id = ct.id
                GROUP BY ct.app_label, ct.model
                ORDER BY count DESC
                LIMIT 10
            """)
            page_types = verify_cur.fetchall()
            print(f"    Page types breakdown:")
            for app_label, model, count in page_types:
                print(f"      - {app_label}.{model}: {count}")
        
        # Check sites
        verify_cur.execute("SELECT COUNT(*) FROM wagtailcore_site")
        site_count = verify_cur.fetchone()[0]
        print(f"  wagtailcore_site: {site_count} rows")
        if site_count == 0:
            print("    ⚠ WARNING: No sites copied!")
            verification_passed = False
        else:
            # Check if site has root_page set
            verify_cur.execute("SELECT COUNT(*) FROM wagtailcore_site WHERE root_page_id IS NOT NULL")
            site_with_root = verify_cur.fetchone()[0]
            print(f"    Sites with root_page: {site_with_root}")
            if site_with_root == 0:
                print("    ⚠ WARNING: No sites have root_page set!")
                verification_passed = False
            else:
                # Show site details
                verify_cur.execute("""
                    SELECT s.id, s.hostname, s.port, s.root_page_id, s.is_default_site,
                           p.title as root_page_title, p.live as root_page_live
                    FROM wagtailcore_site s
                    LEFT JOIN wagtailcore_page p ON s.root_page_id = p.id
                    ORDER BY s.is_default_site DESC, s.id
                """)
                sites = verify_cur.fetchall()
                print(f"    Site details:")
                for site_id, hostname, port, root_page_id, is_default, root_title, root_live in sites:
                    default_str = " (DEFAULT)" if is_default else ""
                    print(f"      - Site {site_id}: {hostname}:{port}{default_str}")
                    if root_page_id:
                        live_str = " (live)" if root_live else " (not live)"
                        print(f"        Root page: {root_title} (ID: {root_page_id}){live_str}")
                    else:
                        print(f"        ⚠ No root page set!")
    
    # Final summary
    print(f"\n" + "=" * 60)
    print(f"Migration Summary")
    print("=" * 60)
    print(f"  Total rows copied: {total_rows}")
    print(f"  Tables processed: {len(tables) - skipped}")
    print(f"  Django system tables skipped: {skipped}")
    
    if not verification_passed:
        print(f"\n⚠ WARNING: Migration verification found issues!")
        print(f"  Some critical tables may be empty or misconfigured.")
        print(f"  The fix_wagtail_site.py script will attempt to fix site configuration.")
        print(f"\n  ACTION REQUIRED: Check the verification output above to see what failed.")
    else:
        print(f"\n✓ Migration verification passed!")
        print(f"  All critical tables appear to have data.")
    
    print(f"\n⚠ Important: After migration, verify:")
    print(f"  1. Wagtail site root page is configured correctly")
    print(f"  2. Pages are accessible in Wagtail admin")
    print(f"  3. Site settings are properly configured")
    
    # Close connections
    source_conn.close()
    dest_conn.close()
    
    print("\nNext steps:")
    print("1. Verify data in Render dashboard")
    print("2. Remove HEROKU_DATABASE_URL after confirming migration success")
    
    return 0 if verification_passed else 1

if __name__ == '__main__':
    sys.exit(main())
