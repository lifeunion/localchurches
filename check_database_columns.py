#!/usr/bin/env python3
"""
Check all columns in wagtailusers_userprofile table to identify any missing ones.
"""
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lampstands.settings.production')
django.setup()

from django.db import connection

def check_userprofile_columns():
    """Check all columns in wagtailusers_userprofile table."""
    with connection.cursor() as cursor:
        # Get all columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns 
            WHERE table_schema = 'public' 
            AND table_name = 'wagtailusers_userprofile'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        
        print("Columns in wagtailusers_userprofile table:")
        print("-" * 80)
        for col in columns:
            print(f"{col[0]:40} {col[1]:20} nullable={col[2]:5} default={col[3] or 'None'}")
        
        # Check specifically for the problematic column
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'wagtailusers_userprofile'
                AND column_name = 'updated_comments_notifications'
            );
        """)
        exists = cursor.fetchone()[0]
        print("\n" + "-" * 80)
        print(f"updated_comments_notifications exists: {exists}")

if __name__ == '__main__':
    check_userprofile_columns()
