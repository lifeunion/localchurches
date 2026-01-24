"""
Django management command to ensure wagtailcore_referenceindex table exists.
Runs migrations if the table is missing (e.g. after Wagtail upgrade).

Usage: python manage.py fix_referenceindex

The ReferenceIndex table is used by Wagtail's page editor to show "Usage" of
images, documents, snippets, etc. in the side panel. It is created by a
Wagtail core migration. If you see:
  ProgrammingError: relation "wagtailcore_referenceindex" does not exist
run this command or `python manage.py migrate` to apply the migration.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Ensure wagtailcore_referenceindex table exists (run migrations if missing)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'wagtailcore_referenceindex'
                );
            """)
            exists = cursor.fetchone()[0]

        if exists:
            self.stdout.write(
                self.style.SUCCESS('Table wagtailcore_referenceindex exists. Nothing to do.')
            )
            return

        self.stdout.write(
            self.style.WARNING(
                'Table wagtailcore_referenceindex does not exist. Running migrate to create it...'
            )
        )
        try:
            call_command('migrate', '--no-input', verbosity=2)
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Migrate failed: {e}')
            )
            raise

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_name = 'wagtailcore_referenceindex'
                );
            """)
            exists_now = cursor.fetchone()[0]

        if exists_now:
            self.stdout.write(
                self.style.SUCCESS('wagtailcore_referenceindex table now exists.')
            )
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Table still missing after migrate. Check: python manage.py showmigrations'
                )
            )
