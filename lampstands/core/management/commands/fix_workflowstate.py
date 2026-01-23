"""
Django management command to fix missing columns in wagtailcore_workflowstate table.
Usage: python manage.py fix_workflowstate
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Add missing columns to wagtailcore_workflowstate table for Wagtail 6.4 compatibility'

    def handle(self, *args, **options):
        """Add missing columns to wagtailcore_workflowstate table if they don't exist."""
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'wagtailcore_workflowstate'
                );
            """)
            table_exists = cursor.fetchone()[0]
            
            if not table_exists:
                self.stdout.write(
                    self.style.WARNING(
                        "Table wagtailcore_workflowstate does not exist. Run migrations first."
                    )
                )
                return
            
            # List of columns that might be missing in Wagtail 6.4
            # Both content_type_id and base_content_type_id are ForeignKeys to django_content_type
            columns_to_add = [
                {
                    'name': 'content_type_id',
                    'type': 'INTEGER',
                    'default': '',
                    'null': 'NULL',
                    'note': 'ForeignKey to django_content_type - nullable'
                },
                {
                    'name': 'base_content_type_id',
                    'type': 'INTEGER',
                    'default': '',
                    'null': 'NULL',
                    'note': 'ForeignKey to django_content_type - nullable (Wagtail 6.4)'
                },
            ]
            
            added_count = 0
            for col in columns_to_add:
                # Check if column exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'wagtailcore_workflowstate'
                        AND column_name = %s
                    );
                """, [col['name']])
                
                column_exists = cursor.fetchone()[0]
                
                if not column_exists:
                    self.stdout.write(f"Adding missing column: {col['name']}")
                    try:
                        # Build ALTER TABLE statement
                        null_clause = col.get('null', 'NOT NULL')
                        default_value = col.get('default', '')
                        if default_value:
                            # Handle empty string defaults
                            if default_value == "''":
                                default_clause = "DEFAULT ''"
                            else:
                                default_clause = f"DEFAULT {default_value}"
                        else:
                            default_clause = ''
                        
                        alter_sql = f"""
                            ALTER TABLE wagtailcore_workflowstate 
                            ADD COLUMN {col['name']} {col['type']} {default_clause} {null_clause};
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
