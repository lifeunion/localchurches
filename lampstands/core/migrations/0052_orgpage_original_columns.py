# Migration: add original lampstands_orgpage columns if missing.
# Original schema (from heroku_dump) had organization_name, office_*, org_contact_*.
# If the table already has these (old DB with data), ADD COLUMN IF NOT EXISTS is a no-op.
# If the table was recreated with only intro/body (0049), this adds the columns (empty).

from django.db import migrations


def add_original_orgpage_columns_if_missing(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        # Original schema columns (from heroku_dump.sql lampstands_orgpage)
        columns = [
            ("organization_name", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("office_state_or_province", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("office_country", "VARCHAR(2) NOT NULL DEFAULT ''"),
            ("office_mailing_address", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("office_meeting_address", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("office_position", "VARCHAR(42) NOT NULL DEFAULT ''"),
            ("office_phone_number", "VARCHAR(25) NOT NULL DEFAULT ''"),
            ("office_fax_number", "VARCHAR(25) NOT NULL DEFAULT ''"),
            ("office_email", "VARCHAR(254) NOT NULL DEFAULT ''"),
            ("office_web", "TEXT NOT NULL DEFAULT ''"),
            ("office_web_2", "TEXT NOT NULL DEFAULT ''"),
            ("last_update", "DATE NULL"),
            ("org_contact_1", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("org_contact_2", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("org_contact_3", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("org_contact_4", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("org_contact_1_phone", "VARCHAR(25) NOT NULL DEFAULT ''"),
            ("org_contact_2_phone", "VARCHAR(25) NOT NULL DEFAULT ''"),
            ("org_contact_3_phone", "VARCHAR(25) NOT NULL DEFAULT ''"),
            ("org_contact_4_phone", "VARCHAR(25) NOT NULL DEFAULT ''"),
        ]
        for col_name, col_def in columns:
            cursor.execute(
                f"ALTER TABLE lampstands_orgpage ADD COLUMN IF NOT EXISTS {col_name} {col_def};"
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0051_orgpage_contact_fields"),
    ]

    operations = [
        migrations.RunPython(add_original_orgpage_columns_if_missing, noop),
    ]
