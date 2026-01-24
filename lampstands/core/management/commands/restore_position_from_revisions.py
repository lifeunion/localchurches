"""
Restore ChurchPage.position from Wagtail revisions after it was overwritten to 39,-98
by the LeafletPanel/LeafletField default (GEO_WIDGET_DEFAULT_LOCATION).

The widget can write the default when the field is considered "empty" by the widget.
Wagtail stores each save in wagtailcore_revision.content (JSON). We find the most
recent revision per ChurchPage that has a non-default position and copy it back to
lampstands_churchpage.position.

Usage:
  python manage.py restore_position_from_revisions           # run restore
  python manage.py restore_position_from_revisions --dry-run # only report, no writes

Other recovery options if this is insufficient:
  - Restore from a Render/Postgres backup from before the overwrite.
  - If you have an export (JSON/CSV) of church data with position, re-import.
"""
import json
import re
from django.core.management.base import BaseCommand
from django.db import connection, transaction

from lampstands.core.models import ChurchPage


# Default from GEO_WIDGET_DEFAULT_LOCATION = {'lat': 39.0, 'lng': -98.0}
# Stored as "39,-98" or "39.0,-98.0" etc.
DEFAULT_POSITION_PATTERN = re.compile(r'^\s*39\.?0*,-98\.?0*\s*$', re.IGNORECASE)


def is_default_position(value):
    if value is None:
        return True
    s = (value or '').strip()
    if not s:
        return True
    return bool(DEFAULT_POSITION_PATTERN.match(s))


class Command(BaseCommand):
    help = (
        "Restore ChurchPage.position from Wagtail revisions where it was overwritten "
        "to the map widget default (39,-98)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only report what would be restored; do not update the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN: no changes will be written.'))

        with connection.cursor() as cursor:
            # Check revision table exists
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = 'wagtailcore_revision'
                );
            """)
            if not cursor.fetchone()[0]:
                self.stdout.write(
                    self.style.ERROR('Table wagtailcore_revision does not exist.')
                )
                return

            # Prefer content; some older Wagtail used content_json
            cursor.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = 'wagtailcore_revision'
                  AND column_name IN ('content', 'content_json')
            """)
            content_cols = [r[0] for r in cursor.fetchall()]
            content_col = 'content' if 'content' in content_cols else (content_cols[0] if content_cols else None)
            if not content_col:
                self.stdout.write(
                    self.style.ERROR('wagtailcore_revision has no content/content_json column.')
                )
                return

            table = ChurchPage._meta.db_table

            # Current positions for ChurchPages (page_ptr_id = page id)
            cursor.execute(f"""
                SELECT page_ptr_id, position FROM {table}
            """)
            cols = [c[0] for c in cursor.description]
            current = {int(r[0]): (r[1] if len(r) > 1 else None) for r in cursor.fetchall()}

            # Revisions for ChurchPages: join via wagtailcore_page so we only get church pages
            # object_id is the page id; content holds JSON with "position"
            cursor.execute(f"""
                SELECT r.object_id, r.{content_col}, r.created_at
                FROM wagtailcore_revision r
                INNER JOIN wagtailcore_page p ON p.id = (r.object_id)::int
                INNER JOIN django_content_type ct ON ct.id = p.content_type_id
                WHERE ct.app_label = 'lampstands' AND ct.model = 'churchpage'
                ORDER BY r.object_id, r.created_at DESC
            """)
            cols = [c[0] for c in cursor.description]
            rows = [dict(zip(cols, r)) for r in cursor.fetchall()]

        # For each page, keep the most recent revision that has a non-default position
        recovered = {}
        for row in rows:
            try:
                page_id = int(row['object_id'])
            except (TypeError, ValueError):
                continue
            if page_id in recovered:
                continue
            raw = row.get(content_col)
            if raw is None:
                continue
            try:
                content = json.loads(raw) if isinstance(raw, str) else raw
            except Exception:
                continue
            if not isinstance(content, dict):
                continue
            pos = content.get('position')
            if is_default_position(pos):
                continue
            recovered[page_id] = pos

        # Only update pages whose current position is the default
        to_update = []
        for page_id, good_pos in recovered.items():
            cur = current.get(page_id)
            if is_default_position(cur):
                to_update.append((page_id, good_pos))

        if not to_update:
            self.stdout.write('No pages need restoring (no good position in revisions, or current is already OK).')
            return

        self.stdout.write(f'Would restore position for {len(to_update)} ChurchPage(s).')
        for page_id, pos in to_update[:20]:
            self.stdout.write(f'  page id {page_id} -> {pos!r}')
        if len(to_update) > 20:
            self.stdout.write(f'  ... and {len(to_update) - 20} more.')

        if dry_run:
            self.stdout.write(self.style.WARNING('Dry run: skipping database updates.'))
            return

        with transaction.atomic():
            with connection.cursor() as cursor:
                for page_id, good_pos in to_update:
                    cursor.execute(
                        f'UPDATE {table} SET position = %s WHERE page_ptr_id = %s',
                        [good_pos, page_id],
                    )
        self.stdout.write(self.style.SUCCESS(f'Restored position for {len(to_update)} ChurchPage(s).'))
