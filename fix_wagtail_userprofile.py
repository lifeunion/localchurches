#!/usr/bin/env python
"""
Fix missing columns in wagtailusers_userprofile table.
This script adds missing columns that Wagtail 6.4 expects.
Run this after database migration from Heroku.
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')
django.setup()

from django.db import connection

def fix_userprofile_columns():
    """Add missing columns to wagtailusers_userprofile table if they don't exist."""
    with connection.cursor() as cursor:
        # Check if table exists
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'wagtailusers_userprofile'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("Table wagtailusers_userprofile does not exist. Run migrations first.")
            return
        
        # List of columns that might be missing in Wagtail 6.4
        columns_to_add = [
            {
                'name': 'updated_comments_notifications',
                'type': 'BOOLEAN',
                'default': 'FALSE',
                'null': 'NOT NULL'
            },
        ]
        
        added_count = 0
        for col in columns_to_add:
            # Check if column exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = 'wagtailusers_userprofile'
                    AND column_name = %s
                );
            """, [col['name']])
            
            column_exists = cursor.fetchone()[0]
            
            if not column_exists:
                print(f"Adding missing column: {col['name']}")
                try:
                    # Add column with default value
                    alter_sql = f"""
                        ALTER TABLE wagtailusers_userprofile 
                        ADD COLUMN {col['name']} {col['type']} DEFAULT {col['default']} {col['null']};
                    """
                    cursor.execute(alter_sql)
                    print(f"✓ Successfully added column: {col['name']}")
                    added_count += 1
                except Exception as e:
                    print(f"✗ Error adding column {col['name']}: {e}")
            else:
                print(f"Column {col['name']} already exists, skipping.")
        
        if added_count > 0:
            print(f"\n✓ Added {added_count} missing column(s).")
        else:
            print("\n✓ All columns already exist. No changes needed.")

if __name__ == '__main__':
    print("Fixing wagtailusers_userprofile table...")
    try:
        fix_userprofile_columns()
        print("\n✓ Fix completed successfully.")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
