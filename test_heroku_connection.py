#!/usr/bin/env python3
"""
Test script to verify connection to Heroku Postgres database.
Run this to check if HEROKU_DATABASE_URL is correct and accessible.
"""
import os
import sys

# Ensure all output is flushed immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Try to import psycopg
try:
    import psycopg
except ImportError:
    print("Installing psycopg...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'psycopg[binary]'])
    import psycopg

def main():
    print("=" * 60)
    print("Testing Heroku Database Connection")
    print("=" * 60)
    
    # Get connection string from environment
    HEROKU_DATABASE_URL = os.environ.get('HEROKU_DATABASE_URL')
    
    if not HEROKU_DATABASE_URL:
        print("\n✗ HEROKU_DATABASE_URL environment variable is not set!")
        print("\nTo set it:")
        print("  export HEROKU_DATABASE_URL='postgres://user:pass@host:port/dbname'")
        print("\nOr in Render dashboard:")
        print("  Go to Environment tab → Add HEROKU_DATABASE_URL")
        return 1
    
    # Mask the password in the URL for display
    masked_url = HEROKU_DATABASE_URL
    if '@' in masked_url:
        parts = masked_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            if len(user_pass) >= 3:  # postgres://user:pass
                masked_url = f"{user_pass[0]}:{user_pass[1]}:****@{parts[1]}"
            elif len(user_pass) == 2:
                masked_url = f"{user_pass[0]}:****@{parts[1]}"
    
    print(f"\nConnection URL (masked): {masked_url}")
    
    # Test connection
    print("\nStep 1: Testing connection...")
    try:
        conn = psycopg.connect(HEROKU_DATABASE_URL)
        print("✓ Successfully connected to Heroku Postgres!")
    except Exception as e:
        print(f"✗ Failed to connect: {e}")
        print(f"  Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Test query
    print("\nStep 2: Testing query...")
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()[0]
            print(f"✓ Database version: {version[:80]}...")
    except Exception as e:
        print(f"✗ Query failed: {e}")
        conn.close()
        return 1
    
    # Get table count
    print("\nStep 3: Checking tables...")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            """)
            table_count = cur.fetchone()[0]
            print(f"✓ Found {table_count} tables in database")
    except Exception as e:
        print(f"✗ Failed to count tables: {e}")
        conn.close()
        return 1
    
    # Check for Wagtail tables
    print("\nStep 4: Checking for Wagtail tables...")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name LIKE 'wagtail%'
                ORDER BY table_name
                LIMIT 10
            """)
            wagtail_tables = [row[0] for row in cur.fetchall()]
            if wagtail_tables:
                print(f"✓ Found {len(wagtail_tables)} Wagtail tables:")
                for table in wagtail_tables:
                    print(f"    - {table}")
            else:
                print("⚠ No Wagtail tables found")
    except Exception as e:
        print(f"✗ Failed to check Wagtail tables: {e}")
    
    # Check for lampstands tables
    print("\nStep 5: Checking for lampstands tables...")
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                AND table_name LIKE 'lampstands%'
                ORDER BY table_name
            """)
            lampstands_tables = [row[0] for row in cur.fetchall()]
            if lampstands_tables:
                print(f"✓ Found {len(lampstands_tables)} lampstands tables:")
                for table in lampstands_tables:
                    print(f"    - {table}")
            else:
                print("⚠ No lampstands tables found")
    except Exception as e:
        print(f"✗ Failed to check lampstands tables: {e}")
    
    # Check page count
    print("\nStep 6: Checking page data...")
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM wagtailcore_page")
            page_count = cur.fetchone()[0]
            print(f"✓ Found {page_count} pages in wagtailcore_page")
            
            if page_count > 0:
                cur.execute("""
                    SELECT COUNT(*) FROM wagtailcore_page p
                    JOIN django_content_type ct ON p.content_type_id = ct.id
                    WHERE ct.app_label = 'lampstands' AND ct.model = 'homepage'
                """)
                homepage_count = cur.fetchone()[0]
                print(f"✓ Found {homepage_count} HomePage instances")
    except Exception as e:
        print(f"⚠ Could not check pages (table may not exist): {e}")
    
    # Close connection
    conn.close()
    
    print("\n" + "=" * 60)
    print("✓ Connection test completed successfully!")
    print("=" * 60)
    print("\nThe database connection is working correctly.")
    print("You can proceed with the migration.")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
