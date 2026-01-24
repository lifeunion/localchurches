"""
Pre-migrate fix for wagtailcore_revision.content JSON when content.content_type
is an ID that no longer exists in django_content_type.

Migration 0071_populate_revision_content_type does:
  Revision.objects.all().update(
      content_type_id=Cast(KeyTextTransform("content_type", models.F("content")), ...)
  )
If content.content_type is 51 and id 51 is not in django_content_type, the
UPDATE violates the FK. This command rewrites such content.content_type to the
Page content type id so 0071 can run.

Usage: python manage.py fix_revision_content_json
Run before migrate (e.g. in build.sh).
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Fix revision content JSON: set content.content_type to Page's when it's missing from django_content_type"

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'wagtailcore_revision'
                );
            """)
            if not cursor.fetchone()[0]:
                self.stdout.write("Table wagtailcore_revision does not exist. Skipping.")
                return

            # Only on PostgreSQL (content::jsonb, jsonb_set)
            if connection.vendor != "postgresql":
                self.stdout.write("Not PostgreSQL. Skipping.")
                return

            sql = """
                UPDATE wagtailcore_revision r
                SET content = jsonb_set(
                    r.content::jsonb,
                    '{content_type}',
                    to_jsonb(ct.id::int)
                )
                FROM django_content_type ct
                WHERE ct.app_label = 'wagtailcore' AND ct.model = 'page'
                  AND r.content IS NOT NULL
                  AND jsonb_typeof(r.content::jsonb) = 'object'
                  AND (r.content::jsonb ? 'content_type')
                  AND (r.content::jsonb->>'content_type') ~ '^[0-9]+$'
                  AND (r.content::jsonb->>'content_type')::int NOT IN (SELECT id FROM django_content_type)
            """
            cursor.execute(sql)
            n = cursor.rowcount
        if n and n > 0:
            self.stdout.write(self.style.SUCCESS(f"Updated {n} revision(s) with invalid content.content_type."))
        else:
            self.stdout.write("No revisions with invalid content.content_type.")
