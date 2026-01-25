# Migration: convert PrivacyPage.content from CharField back to StreamField
# so stored wholestory/raw_html JSON is rendered as HTML instead of raw text.

from django.db import migrations

import wagtail.fields
from lampstands.core.models import StoryBlock


def empty_to_list(apps, schema_editor):
    """Convert empty or blank content to '[]' so the JSON column can parse it."""
    PrivacyPage = apps.get_model("lampstands", "PrivacyPage")
    updated = PrivacyPage.objects.filter(content="").update(content="[]")
    if updated:
        # Also catch whitespace-only; update() with content='' would not match
        for p in PrivacyPage.objects.all():
            if not (p.content and str(p.content).strip()):
                p.content = "[]"
                p.save()


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0041_orgindexpage"),
    ]

    operations = [
        migrations.RunPython(empty_to_list, noop),
        migrations.AlterField(
            model_name="privacypage",
            name="content",
            field=wagtail.fields.StreamField(
                [("wholestory", StoryBlock())],
                blank=True,
                use_json_field=True,
            ),
        ),
    ]
