#!/usr/bin/env python3
"""
Direct database fix script - connects to Render database and adds missing column.
This can be run locally if you have the DATABASE_URL.
"""
import os
import sys
import psycopg
from urllib.parse import urlparse

def fix_userprofile_column(database_url):
    """Connect to database and add missing column."""
    try:
        # Parse the database URL
        parsed = urlparse(database_url)
        
        # Connect to database
        conn = psycopg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            dbname=parsed.path.lstrip('/')
        )
        
        with conn.cursor() as cursor:
            # Check if column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'wagtailusers_userprofile'
                    AND column_name = 'updated_comments_notifications'
                );
            """)
            
            column_exists = cursor.fetchone()[0]
            
            if not column_exists:
                print("Adding missing column: updated_comments_notifications")
                cursor.execute("""
                    ALTER TABLE wagtailusers_userprofile 
                    ADD COLUMN updated_comments_notifications BOOLEAN DEFAULT FALSE NOT NULL;
                """)
                conn.commit()
                print("✓ Successfully added column!")
            else:
                print("✓ Column already exists.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == '__main__':
    # Get DATABASE_URL from environment or command line
    database_url = os.environ.get('DATABASE_URL') or (sys.argv[1] if len(sys.argv) > 1 else None)
    
    if not database_url:
        print("Usage: python fix_database_direct.py <DATABASE_URL>")
        print("Or set DATABASE_URL environment variable")
        sys.exit(1)
    
    print("Connecting to database...")
    if fix_userprofile_column(database_url):
        print("\n✓ Fix completed successfully!")
        sys.exit(0)
    else:
        print("\n✗ Fix failed!")
        sys.exit(1)
