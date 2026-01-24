"""
Django management command to ensure wagtailcore_referenceindex table exists.
Runs migrations if the table is missing (e.g. after Wagtail upgrade). If
migrate does not create it (e.g. migration already marked applied), creates
the table via Django's schema editor.

Usage: python manage.py fix_referenceindex

The ReferenceIndex table is used by Wagtail's page editor to show "Usage" of
images, documents, snippets, etc. in the side panel. If you see:
  ProgrammingError: relation "wagtailcore_referenceindex" does not exist
run this command.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


def _table_exists(cursor):
    cursor.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'wagtailcore_referenceindex'
        );
    """)
    return cursor.fetchone()[0]


class Command(BaseCommand):
    help = 'Ensure wagtailcore_referenceindex table exists (run migrations if missing)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            if _table_exists(cursor):
                self.stdout.write(
                    self.style.SUCCESS('Table wagtailcore_referenceindex exists. Nothing to do.')
                )
                return

        self.stdout.write(
            self.style.WARNING(
                'Table wagtailcore_referenceindex does not exist. Running migrate...'
            )
        )
        try:
            call_command('migrate', '--no-input', verbosity=2)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Migrate failed: {e}'))
            raise

        with connection.cursor() as cursor:
            if _table_exists(cursor):
                self.stdout.write(
                    self.style.SUCCESS('wagtailcore_referenceindex table now exists.')
                )
                return

        self.stdout.write(
            self.style.WARNING(
                'Table still missing after migrate (migration may be marked applied). '
                'Creating table via schema editor...'
            )
        )
        try:
            from wagtail.models.reference_index import ReferenceIndex
            with connection.schema_editor() as schema_editor:
                schema_editor.create_model(ReferenceIndex)
            self.stdout.write(
                self.style.SUCCESS('Created wagtailcore_referenceindex table.')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Could not create table: {e}')
            )
            raise
