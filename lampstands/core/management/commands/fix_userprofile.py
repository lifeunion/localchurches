"""
Django management command to fix missing columns in wagtailusers_userprofile table.
Usage: python manage.py fix_userprofile
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add missing columns to wagtailusers_userprofile table for Wagtail 6.4 compatibility'

    def handle(self, *args, **options):
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
                self.stdout.write(
                    self.style.WARNING(
                        "Table wagtailusers_userprofile does not exist. Run migrations first."
                    )
                )
                return
            
            # List of columns that might be missing in Wagtail 6.4
            # Based on error logs and Wagtail 6.4 UserProfile model
            columns_to_add = [
                {
                    'name': 'updated_comments_notifications',
                    'type': 'BOOLEAN',
                    'default': 'FALSE',
                    'null': 'NOT NULL'
                },
                {
                    'name': 'rejected_notifications',
                    'type': 'BOOLEAN',
                    'default': 'FALSE',
                    'null': 'NOT NULL'
                },
                {
                    'name': 'current_time_zone',
                    'type': 'VARCHAR(40)',
                    'default': "''",
                    'null': 'NOT NULL'
                },
                {
                    'name': 'preferred_language',
                    'type': 'VARCHAR(10)',
                    'default': "''",
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
                    self.stdout.write(f"Adding missing column: {col['name']}")
                    try:
                        # Add column with default value
                        alter_sql = f"""
                            ALTER TABLE wagtailusers_userprofile 
                            ADD COLUMN {col['name']} {col['type']} DEFAULT {col['default']} {col['null']};
                        """
                        cursor.execute(alter_sql)
                        self.stdout.write(
                            self.style.SUCCESS(f"✓ Successfully added column: {col['name']}")
                        )
                        added_count += 1
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(f"✗ Error adding column {col['name']}: {e}")
                        )
                else:
                    self.stdout.write(f"Column {col['name']} already exists, skipping.")
            
            if added_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f"\n✓ Added {added_count} missing column(s).")
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✓ All columns already exist. No changes needed.")
                )
