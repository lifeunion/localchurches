"""
Django management command to ensure lampstands_orgpage has intro and body columns.
Fixes: ProgrammingError: column lampstands_orgpage.intro does not exist

Usage: python manage.py fix_orgpage

Run during build (build.sh) so the admin explorer for "Organizations listing" works
even when migrations 0049/0050 were already applied without adding the columns
(e.g. table existed from an older migration).
"""
from django.core.management.base import BaseCommand
from django.db import connection


def _table_exists(cursor):
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'lampstands_orgpage'
        );
    """)
    return cursor.fetchone()[0]


def _column_exists(cursor, column_name):
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'lampstands_orgpage'
            AND column_name = %s
        );
    """, [column_name])
    return cursor.fetchone()[0]


class Command(BaseCommand):
    help = 'Ensure lampstands_orgpage has intro and body columns (fixes admin Organization listing 500)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            if not _table_exists(cursor):
                self.stdout.write(
                    self.style.WARNING(
                        'Table lampstands_orgpage does not exist. Run migrations first.'
                    )
                )
                return

            added = 0
            if not _column_exists(cursor, 'intro'):
                self.stdout.write('Adding missing column: intro')
                cursor.execute("""
                    ALTER TABLE lampstands_orgpage
                    ADD COLUMN intro TEXT NOT NULL DEFAULT '';
                """)
                added += 1
                self.stdout.write(self.style.SUCCESS('  Added intro'))
            if not _column_exists(cursor, 'body'):
                self.stdout.write('Adding missing column: body')
                cursor.execute("""
                    ALTER TABLE lampstands_orgpage
                    ADD COLUMN body TEXT NOT NULL DEFAULT '';
                """)
                added += 1
                self.stdout.write(self.style.SUCCESS('  Added body'))

            # Original org page columns (from heroku_dump / migration 0052) so existing data is readable
            original_columns = [
                ('organization_name', 'VARCHAR(255) NOT NULL DEFAULT \'\''),
                ('office_state_or_province', 'VARCHAR(255) NOT NULL DEFAULT \'\''),
                ('office_country', 'VARCHAR(2) NOT NULL DEFAULT \'\''),
                ('office_mailing_address', 'VARCHAR(255) NOT NULL DEFAULT \'\''),
                ('office_meeting_address', 'VARCHAR(255) NOT NULL DEFAULT \'\''),
                ('office_position', 'VARCHAR(42) NOT NULL DEFAULT \'\''),
                ('office_phone_number', 'VARCHAR(25) NOT NULL DEFAULT \'\''),
                ('office_fax_number', 'VARCHAR(25) NOT NULL DEFAULT \'\''),
                ('office_email', 'VARCHAR(254) NOT NULL DEFAULT \'\''),
                ('office_web', 'TEXT NOT NULL DEFAULT \'\''),
                ('office_web_2', 'TEXT NOT NULL DEFAULT \'\''),
                ('last_update', 'DATE NULL'),
                ('org_contact_1', 'VARCHAR(255) NOT NULL DEFAULT \'\''),
                ('org_contact_2', 'VARCHAR(255) NOT NULL DEFAULT \'\''),
                ('org_contact_3', 'VARCHAR(255) NOT NULL DEFAULT \'\''),
                ('org_contact_4', 'VARCHAR(255) NOT NULL DEFAULT \'\''),
                ('org_contact_1_phone', 'VARCHAR(25) NOT NULL DEFAULT \'\''),
                ('org_contact_2_phone', 'VARCHAR(25) NOT NULL DEFAULT \'\''),
                ('org_contact_3_phone', 'VARCHAR(25) NOT NULL DEFAULT \'\''),
                ('org_contact_4_phone', 'VARCHAR(25) NOT NULL DEFAULT \'\''),
            ]
            for col_name, col_def in original_columns:
                if not _column_exists(cursor, col_name):
                    self.stdout.write(f'Adding missing column: {col_name}')
                    cursor.execute(
                        f"ALTER TABLE lampstands_orgpage ADD COLUMN {col_name} {col_def};"
                    )
                    added += 1
                    self.stdout.write(self.style.SUCCESS(f'  Added {col_name}'))

            if added:
                self.stdout.write(
                    self.style.SUCCESS(f'fix_orgpage: added {added} column(s).')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('fix_orgpage: all columns already exist. Nothing to do.')
                )
