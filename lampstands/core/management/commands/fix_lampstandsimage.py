"""
Django management command to add missing columns to lampstands_lampstandsimage table.

This is needed after migrating from Heroku to Render or upgrading Wagtail versions,
where the database schema may not match the model definition.
"""
from django.core.management.base import BaseCommand
from django.db import connection
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Add missing columns to lampstands_lampstandsimage table for Wagtail 6.4 compatibility'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = 'lampstands_lampstandsimage'
                );
            """)
            table_exists = cursor.fetchone()[0]

            if not table_exists:
                self.stdout.write(
                    self.style.WARNING('Table lampstands_lampstandsimage does not exist. Skipping.')
                )
                return

            # List of columns that might be missing (from Wagtail AbstractImage)
            columns_to_add = [
                {
                    'name': 'description',
                    'type': 'TEXT',
                    'default': '',
                    'null': 'NULL',
                    'note': 'Image description field from Wagtail AbstractImage - nullable'
                },
            ]

            added_count = 0
            skipped_count = 0

            for col in columns_to_add:
                # Check if column already exists
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'lampstands_lampstandsimage'
                        AND column_name = %s
                    );
                """, [col['name']])

                column_exists = cursor.fetchone()[0]

                if column_exists:
                    self.stdout.write(
                        self.style.SUCCESS(f'Column {col["name"]} already exists. Skipping.')
                    )
                    skipped_count += 1
                    continue

                # Add the column
                try:
                    sql = f"""
                        ALTER TABLE lampstands_lampstandsimage 
                        ADD COLUMN {col['name']} {col['type']} {col['null']};
                    """
                    cursor.execute(sql)
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✅ Added column {col["name"]} ({col["type"]} {col["null"]}) - {col["note"]}'
                        )
                    )
                    added_count += 1
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'❌ Failed to add column {col["name"]}: {str(e)}'
                        )
                    )

            # Summary
            self.stdout.write('')
            if added_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Successfully added {added_count} column(s)')
                )
            if skipped_count > 0:
                self.stdout.write(
                    self.style.WARNING(f'⏭️  Skipped {skipped_count} existing column(s)')
                )
            if added_count == 0 and skipped_count == 0:
                self.stdout.write(
                    self.style.WARNING('No columns to add or modify.')
                )

            # Verify the columns exist
            self.stdout.write('')
            self.stdout.write('Verifying columns...')
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'lampstands_lampstandsimage'
                AND column_name IN ('description')
                ORDER BY column_name;
            """)
            results = cursor.fetchall()
            if results:
                self.stdout.write(self.style.SUCCESS('✅ Verified columns exist:'))
                for row in results:
                    self.stdout.write(f'   - {row[0]} ({row[1]}, nullable: {row[2]})')
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️  Could not verify columns (this may be normal)')
                )
