# Migration: register consented_brother_* fields in Django state (columns already exist in DB from heroku_dump).
# Uses SeparateDatabaseAndState so we do not try to create columns that already exist.

from django.db import migrations, models


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0055_churchpage_map_search_address"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="churchpage",
                    name="consented_brother_1",
                    field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Consented contact 1 (name)"),
                ),
                migrations.AddField(
                    model_name="churchpage",
                    name="consented_brother_1_phone",
                    field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Consented contact 1 (phone)"),
                ),
                migrations.AddField(
                    model_name="churchpage",
                    name="consented_brother_2",
                    field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Consented contact 2 (name)"),
                ),
                migrations.AddField(
                    model_name="churchpage",
                    name="consented_brother_2_phone",
                    field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Consented contact 2 (phone)"),
                ),
                migrations.AddField(
                    model_name="churchpage",
                    name="consented_brother_3",
                    field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Consented contact 3 (name)"),
                ),
                migrations.AddField(
                    model_name="churchpage",
                    name="consented_brother_3_phone",
                    field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Consented contact 3 (phone)"),
                ),
                migrations.AddField(
                    model_name="churchpage",
                    name="consented_brother_4",
                    field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Consented contact 4 (name)"),
                ),
                migrations.AddField(
                    model_name="churchpage",
                    name="consented_brother_4_phone",
                    field=models.CharField(blank=True, max_length=255, null=True, verbose_name="Consented contact 4 (phone)"),
                ),
            ],
            database_operations=[
                migrations.RunPython(noop, noop),
            ],
        ),
    ]
