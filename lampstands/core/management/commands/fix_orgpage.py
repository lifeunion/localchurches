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

            if added:
                self.stdout.write(
                    self.style.SUCCESS(f'fix_orgpage: added {added} column(s).')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('fix_orgpage: intro and body already exist. Nothing to do.')
                )
