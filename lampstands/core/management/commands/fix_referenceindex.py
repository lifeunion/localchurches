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

        # Do not run migrate here: it can trigger 0071_populate_revision_content_type, which
        # fails when revision.content.content_type references a missing django_content_type
        # (e.g. id 51). build.sh already runs migrate; we only create the table if it's missing.
        self.stdout.write(
            self.style.WARNING(
                'Table is missing. Creating via schema editor or raw SQL...'
            )
        )

        # 1) Try schema_editor first (matches Wagtail's ReferenceIndex model exactly).
        try:
            from wagtail.models.reference_index import ReferenceIndex
            with connection.schema_editor() as se:
                se.create_model(ReferenceIndex)
            with connection.cursor() as cursor:
                if _table_exists(cursor):
                    self.stdout.write(
                        self.style.SUCCESS('Created wagtailcore_referenceindex table (schema editor).')
                    )
                    return
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Schema editor could not create table: {e}')
            )

        # 2) Fallback: raw SQL matching Wagtail 6.4 migration 0078_referenceindex.
        #    Used when migration is marked applied but table was never created (e.g. faked, DB restore).
        self.stdout.write('Creating wagtailcore_referenceindex via raw SQL...')
        raw_sql = """
            CREATE TABLE IF NOT EXISTS wagtailcore_referenceindex (
                id SERIAL PRIMARY KEY,
                object_id VARCHAR(255) NOT NULL,
                to_object_id VARCHAR(255) NOT NULL,
                model_path TEXT NOT NULL,
                content_path TEXT NOT NULL,
                content_path_hash UUID NOT NULL,
                base_content_type_id INTEGER NOT NULL REFERENCES django_content_type(id) ON DELETE CASCADE,
                content_type_id INTEGER NOT NULL REFERENCES django_content_type(id) ON DELETE CASCADE,
                to_content_type_id INTEGER NOT NULL REFERENCES django_content_type(id) ON DELETE CASCADE,
                UNIQUE (base_content_type_id, object_id, to_content_type_id, to_object_id, content_path_hash)
            );
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(raw_sql)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Raw SQL could not create table: {e}'))
            raise

        with connection.cursor() as cursor:
            if _table_exists(cursor):
                self.stdout.write(
                    self.style.SUCCESS('Created wagtailcore_referenceindex table (raw SQL).')
                )
            else:
                self.stdout.write(
                    self.style.ERROR('Table still missing after raw SQL CREATE.')
                )
                raise RuntimeError('wagtailcore_referenceindex was not created.')
