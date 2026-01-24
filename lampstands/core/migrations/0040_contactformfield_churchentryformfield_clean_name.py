# Generated migration: add clean_name to form field models (required by Wagtail AbstractFormField)

from django.db import migrations, models


def backfill_clean_name(apps, schema_editor):
    from wagtail.contrib.forms.utils import get_field_clean_name

    ContactFormField = apps.get_model("lampstands", "ContactFormField")
    ChurchentryFormField = apps.get_model("lampstands", "ChurchentryFormField")

    for obj in ContactFormField.objects.all():
        if not obj.clean_name and obj.label:
            obj.clean_name = get_field_clean_name(obj.label)
            obj.save(update_fields=["clean_name"])

    for obj in ChurchentryFormField.objects.all():
        if not obj.clean_name and obj.label:
            obj.clean_name = get_field_clean_name(obj.label)
            obj.save(update_fields=["clean_name"])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0039_auto_20180120_2228"),
    ]

    operations = [
        migrations.AddField(
            model_name="contactformfield",
            name="clean_name",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Safe name of the form field, the label converted to ascii_snake_case",
                max_length=255,
                verbose_name="name",
            ),
        ),
        migrations.AddField(
            model_name="churchentryformfield",
            name="clean_name",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Safe name of the form field, the label converted to ascii_snake_case",
                max_length=255,
                verbose_name="name",
            ),
        ),
        migrations.RunPython(backfill_clean_name, noop),
    ]
