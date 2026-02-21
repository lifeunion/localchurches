# Migration: ensure lampstands_orgpage has intro and body columns.
# Fixes "column lampstands_orgpage.intro does not exist" when the table existed
# before 0049 (e.g. from an older migration) so CreateModel in 0049 was skipped or failed.
# Safety net: add columns if a previous 0049 run left the table without them.

from django.db import migrations


def add_orgpage_columns_if_missing(apps, schema_editor):
    # PostgreSQL: add columns only if they don't exist (safe when 0049 already ran).
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            ALTER TABLE lampstands_orgpage
            ADD COLUMN IF NOT EXISTS intro TEXT NOT NULL DEFAULT '';
            """
        )
        cursor.execute(
            """
            ALTER TABLE lampstands_orgpage
            ADD COLUMN IF NOT EXISTS body TEXT NOT NULL DEFAULT '';
            """
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0049_orgpage_intro_body"),
    ]

    operations = [
        migrations.RunPython(add_orgpage_columns_if_missing, noop),
    ]
