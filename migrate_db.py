#!/usr/bin/env python3
"""
Database migration script using Python/psycopg to avoid version mismatch issues.
Migrates data from Heroku Postgres to Render Postgres.
"""
import os
import sys
import psycopg
from psycopg import sql

# Connection strings - set via environment (no hardcoded secrets)
HEROKU_DB = os.environ.get('HEROKU_DATABASE_URL')
RENDER_DB = os.environ.get('RENDER_DATABASE_URL')

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

def get_table_columns(conn, table_name):
    """Get column names for a table."""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))
        return cur.fetchall()

def copy_table_data(source_conn, dest_conn, table_name):
    """Copy data from source to destination table."""
    print(f"  Copying {table_name}...", end=' ', flush=True)
    
    try:
        # Get data from source
        with source_conn.cursor() as src_cur:
            src_cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table_name)))
            columns = [desc[0] for desc in src_cur.description]
            rows = src_cur.fetchall()
        
        if not rows:
            print("(empty)")
            return 0
        
        # Insert into destination
        with dest_conn.cursor() as dest_cur:
            # Build INSERT statement
            cols = sql.SQL(', ').join(map(sql.Identifier, columns))
            placeholders = sql.SQL(', ').join(sql.Placeholder() * len(columns))
            insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                cols,
                placeholders
            )
            
            dest_cur.executemany(insert_query, rows)
            dest_conn.commit()
            print(f"✓ ({len(rows)} rows)")
            return len(rows)
    except Exception as e:
        print(f"✗ Error: {e}")
        dest_conn.rollback()
        return 0

def main():
    print("Database Migration: Heroku Postgres → Render Postgres")
    print("=" * 60)
    
    if not HEROKU_DB:
        print("Error: HEROKU_DATABASE_URL not set. export HEROKU_DATABASE_URL='postgres://...'")
        sys.exit(1)
    if not RENDER_DB:
        print("Error: RENDER_DATABASE_URL not set. export RENDER_DATABASE_URL='postgresql://...'")
        sys.exit(1)
    
    # Connect to databases
    print("\nStep 1: Connecting to databases...")
    try:
        source_conn = psycopg.connect(HEROKU_DB)
        print("✓ Connected to Heroku Postgres")
    except Exception as e:
        print(f"✗ Failed to connect to Heroku: {e}")
        sys.exit(1)
    
    try:
        dest_conn = psycopg.connect(RENDER_DB)
        print("✓ Connected to Render Postgres")
    except Exception as e:
        print(f"✗ Failed to connect to Render: {e}")
        source_conn.close()
        sys.exit(1)
    
    # Get list of tables
    print("\nStep 2: Discovering tables...")
    try:
        tables = get_all_tables(source_conn)
        print(f"✓ Found {len(tables)} tables")
    except Exception as e:
        print(f"✗ Error getting tables: {e}")
        source_conn.close()
        dest_conn.close()
        sys.exit(1)
    
    # Copy data
    print("\nStep 3: Copying data...")
    total_rows = 0
    for table in tables:
        # Skip Django/Wagtail system tables that will be created by migrations
        if table.startswith('django_') or table.startswith('wagtail_'):
            print(f"  Skipping {table} (will be created by migrations)")
            continue
        rows = copy_table_data(source_conn, dest_conn, table)
        total_rows += rows
    
    print(f"\n✓ Migration complete! Copied {total_rows} total rows")
    
    # Close connections
    source_conn.close()
    dest_conn.close()
    
    print("\nNext steps:")
    print("1. Link the database to your web service in Render dashboard")
    print("2. Run migrations: python manage.py migrate")
    print("3. Deploy your app")

if __name__ == '__main__':
    main()
