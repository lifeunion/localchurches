"""
Check whether lampstands_churchpage has consented_* columns (from heroku_dump schema).

Usage: python manage.py check_churchpage_columns
"""
from django.core.management.base import BaseCommand
from django.db import connection


CONSENTED_COLUMNS = [
    'consented_brother_1',
    'consented_brother_1_phone',
    'consented_brother_2',
    'consented_brother_2_phone',
    'consented_brother_3',
    'consented_brother_3_phone',
    'consented_brother_4',
    'consented_brother_4_phone',
]


class Command(BaseCommand):
    help = 'Check if lampstands_churchpage has consented_brother_* columns'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'lampstands_churchpage'
                );
            """)
            if not cursor.fetchone()[0]:
                self.stdout.write(
                    self.style.WARNING('Table lampstands_churchpage does not exist.')
                )
                return

            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'lampstands_churchpage'
                ORDER BY ordinal_position;
            """)
            all_columns = [row[0] for row in cursor.fetchall()]

        consented_found = [c for c in CONSENTED_COLUMNS if c in all_columns]
        consented_missing = [c for c in CONSENTED_COLUMNS if c not in all_columns]

        self.stdout.write('lampstands_churchpage columns (contact-related):')
        contact_cols = [c for c in all_columns if 'brother' in c or 'consent' in c.lower()]
        for col in sorted(contact_cols):
            self.stdout.write('  ' + col)

        self.stdout.write('')
        if consented_found:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Consented columns present ({len(consented_found)}/8): ' + ', '.join(consented_found)
                )
            )
        if consented_missing:
            self.stdout.write(
                self.style.WARNING(
                    f'Consented columns missing ({len(consented_missing)}/8): ' + ', '.join(consented_missing)
                )
            )
        if not consented_found and not consented_missing:
            self.stdout.write(self.style.WARNING('No consented_* columns defined to check.'))

        if len(consented_found) == 8:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Database has all consented_brother_* columns.'))
        elif consented_missing:
            self.stdout.write('')
            self.stdout.write(
                self.style.NOTICE(
                    'Database does NOT have consented_* columns. '
                    'Add them via a migration if you need to match heroku_dump / restore data.'
                )
            )
