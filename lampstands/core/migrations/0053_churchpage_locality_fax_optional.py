# Migration: make locality_fax_number optional (allow NULL / default '') so creating
# a new ChurchPage without fax no longer raises NotNullViolation.

from django.db import migrations, models


def make_locality_fax_optional(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.columns
                WHERE table_schema = 'public'
                AND table_name = 'lampstands_churchpage'
                AND column_name = 'locality_fax_number'
            );
        """)
        if cursor.fetchone()[0]:
            cursor.execute("""
                ALTER TABLE lampstands_churchpage
                ALTER COLUMN locality_fax_number DROP NOT NULL,
                ALTER COLUMN locality_fax_number SET DEFAULT '';
            """)
        else:
            cursor.execute("""
                ALTER TABLE lampstands_churchpage
                ADD COLUMN locality_fax_number VARCHAR(25) DEFAULT '' NULL;
            """)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0052_orgpage_original_columns"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="churchpage",
                    name="locality_fax_number",
                    field=models.CharField(blank=True, max_length=25, null=True),
                ),
            ],
            database_operations=[
                migrations.RunPython(make_locality_fax_optional, noop),
            ],
        ),
    ]
