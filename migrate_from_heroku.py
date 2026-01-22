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


def copy_table_data(source_conn, dest_conn, table_name, skip_columns=None, json_columns=None, filter_null_columns=None):
    """Copy data from source to destination table."""
    print(f"  Copying {table_name}...", end=' ', flush=True)
    json_columns = json_columns or []
    filter_null_columns = filter_null_columns or []
    
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
        
        # Transform rows: wrap json_columns values in Jsonb for psycopg
        json_indices = {i for i, c in enumerate(common_columns) if c in json_columns}
        if json_indices:
            def adapt_row(row):
                r = list(row)
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
            # Build INSERT statement with ON CONFLICT DO NOTHING to avoid duplicates
            cols = sql.SQL(', ').join(map(sql.Identifier, common_columns))
            placeholders = sql.SQL(', ').join(sql.Placeholder() * len(common_columns))
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
                sql.Identifier(table_name),
                cols,
                placeholders
            )
            
            try:
                dest_cur.executemany(insert_query, rows)
                dest_conn.commit()
                print(f"✓ ({len(rows)} rows)")
                return len(rows)
            except Exception as batch_error:
                # If batch insert fails, try row-by-row to identify problematic rows
                dest_conn.rollback()
                print(f"(batch insert failed, trying row-by-row...) ", end='', flush=True)
                successful = 0
                failed = 0
                for row in rows:
                    try:
                        dest_cur.execute(insert_query, row)
                        successful += 1
                    except Exception as row_error:
                        failed += 1
                        # Only print first few errors to avoid spam
                        if failed <= 3:
                            error_msg = str(row_error)
                            print(f"\n    Row error: {error_msg[:100]}", end='', flush=True)
                dest_conn.commit()
                if successful > 0:
                    print(f"✓ ({successful} rows, {failed} failed)")
                    return successful
                else:
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
    
    # Track which revision IDs were successfully copied (for fixing page references)
    copied_revision_ids = set()
    
    for table in wagtail_tables_order:
        if table in tables:
            # For wagtailcore_revision, handle JSON content column properly and filter NULL content_type_id
            skip_cols = None
            json_cols = None
            filter_null_cols = None
            if table == 'wagtailcore_revision':
                json_cols = ['content']  # Wrap content in Jsonb for proper JSON serialization
                filter_null_cols = ['content_type_id']  # Filter out rows with NULL content_type_id (NOT NULL constraint)
            
            rows = copy_table_data(source_conn, dest_conn, table, skip_columns=skip_cols, json_columns=json_cols, filter_null_columns=filter_null_cols)
            total_rows += rows
            
            # If we copied revisions, track their IDs for later use
            if table == 'wagtailcore_revision' and rows > 0:
                # Get list of revision IDs that were copied
                try:
                    with dest_conn.cursor() as cur:
                        cur.execute("SELECT id FROM wagtailcore_revision")
                        copied_revision_ids = {row[0] for row in cur.fetchall()}
                        print(f"  Tracked {len(copied_revision_ids)} revision IDs")
                except Exception as e:
                    print(f"  Warning: Could not track revision IDs: {e}")
            
            # For wagtailcore_page, fix live_revision_id references to revisions that don't exist
            if table == 'wagtailcore_page' and copied_revision_ids:
                try:
                    with dest_conn.cursor() as cur:
                        # Set live_revision_id to NULL for pages referencing non-existent revisions
                        cur.execute("""
                            UPDATE wagtailcore_page 
                            SET live_revision_id = NULL 
                            WHERE live_revision_id IS NOT NULL 
                            AND live_revision_id NOT IN (SELECT id FROM wagtailcore_revision)
                        """)
                        fixed_count = cur.rowcount
                        if fixed_count > 0:
                            print(f"  Fixed {fixed_count} pages with invalid live_revision_id references")
                        dest_conn.commit()
                except Exception as e:
                    print(f"  Warning: Could not fix page revision references: {e}")
                    dest_conn.rollback()
    
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
    
    print(f"\n✓ Migration complete!")
    print(f"  Copied {total_rows} total rows from {len(tables) - skipped} tables")
    print(f"  Skipped {skipped} Django system tables")
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
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
