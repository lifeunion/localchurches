# Migration: add contact and address fields to OrgPage (phone, email, address, website, etc.)
# Uses ADD COLUMN IF NOT EXISTS so re-running or DBs that already have these columns do not fail.

from django.db import migrations, models


def add_orgpage_contact_columns_if_missing(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        columns = [
            ("phone", "VARCHAR(50) NOT NULL DEFAULT ''"),
            ("fax", "VARCHAR(50) NOT NULL DEFAULT ''"),
            ("email", "VARCHAR(254) NOT NULL DEFAULT ''"),
            ("website", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("address", "TEXT NOT NULL DEFAULT ''"),
            ("contact_name", "VARCHAR(255) NOT NULL DEFAULT ''"),
            ("contact_phone", "VARCHAR(50) NOT NULL DEFAULT ''"),
        ]
        for col_name, col_def in columns:
            cursor.execute(
                f"ALTER TABLE lampstands_orgpage ADD COLUMN IF NOT EXISTS {col_name} {col_def};"
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0050_orgpage_add_intro_body_if_missing"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="orgpage",
                    name="phone",
                    field=models.CharField(blank=True, default="", help_text="Phone number", max_length=50),
                ),
                migrations.AddField(
                    model_name="orgpage",
                    name="fax",
                    field=models.CharField(blank=True, default="", help_text="Fax number", max_length=50),
                ),
                migrations.AddField(
                    model_name="orgpage",
                    name="email",
                    field=models.EmailField(blank=True, default="", help_text="Email address", max_length=254),
                ),
                migrations.AddField(
                    model_name="orgpage",
                    name="website",
                    field=models.URLField(blank=True, default="", help_text="Organization website (include https://)", max_length=255),
                ),
                migrations.AddField(
                    model_name="orgpage",
                    name="address",
                    field=models.TextField(blank=True, default="", help_text="Street address, city, state, postal code"),
                ),
                migrations.AddField(
                    model_name="orgpage",
                    name="contact_name",
                    field=models.CharField(blank=True, default="", help_text="Primary contact person name", max_length=255),
                ),
                migrations.AddField(
                    model_name="orgpage",
                    name="contact_phone",
                    field=models.CharField(blank=True, default="", help_text="Primary contact phone", max_length=50),
                ),
            ],
            database_operations=[
                migrations.RunPython(add_orgpage_contact_columns_if_missing, noop),
            ],
        ),
    ]
