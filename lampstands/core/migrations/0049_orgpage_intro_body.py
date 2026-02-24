# Migration: add OrgPage model with intro/body so legacy org pages can be edited and display content.
# Backfills rows for existing pages that have content_type lampstands.orgpage.
# DB operations are idempotent: create table if not exists, add intro/body columns if missing,
# so this migration succeeds even when lampstands_orgpage already existed (e.g. from an older migration).

import django.db.models.deletion
from django.db import migrations, models


def ensure_orgpage_table_and_columns(apps, schema_editor):
    """Create lampstands_orgpage with intro/body if missing; add columns if table exists without them."""
    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS lampstands_orgpage (
                page_ptr_id integer NOT NULL PRIMARY KEY REFERENCES wagtailcore_page(id) ON DELETE CASCADE,
                intro TEXT NOT NULL DEFAULT '',
                body TEXT NOT NULL DEFAULT ''
            );
            """
        )
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


def backfill_orgpage_rows(apps, schema_editor):
    # Do not use apps.get_model("lampstands", "OrgPage") here: with SeparateDatabaseAndState,
    # state_operations (CreateModel OrgPage) are applied after database_operations, so OrgPage
    # is not in the app registry yet. Use raw SQL against lampstands_orgpage instead.
    ContentType = apps.get_model("contenttypes", "ContentType")
    ct = ContentType.objects.filter(app_label="lampstands", model="orgpage").first()
    if not ct:
        return

    with schema_editor.connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO lampstands_orgpage (page_ptr_id, intro, body)
            SELECT p.id, '', ''
            FROM wagtailcore_page p
            WHERE p.content_type_id = %s
            AND NOT EXISTS (
                SELECT 1 FROM lampstands_orgpage o WHERE o.page_ptr_id = p.id
            );
            """,
            [ct.id],
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0048_churchpage_locality_country_optional"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name="OrgPage",
                    fields=[
                        (
                            "page_ptr",
                            models.OneToOneField(
                                auto_created=True,
                                on_delete=django.db.models.deletion.CASCADE,
                                parent_link=True,
                                primary_key=True,
                                serialize=False,
                                to="wagtailcore.page",
                            ),
                        ),
                        ("intro", models.TextField(blank=True)),
                        ("body", models.TextField(blank=True)),
                    ],
                    options={
                        "verbose_name": "Organization page (legacy)",
                        "abstract": False,
                    },
                    bases=("wagtailcore.page",),
                ),
            ],
            database_operations=[
                migrations.RunPython(ensure_orgpage_table_and_columns, noop),
                migrations.RunPython(backfill_orgpage_rows, noop),
            ],
        ),
    ]
