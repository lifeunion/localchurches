# Migration: add file_hash to LampstandsImage to match Wagtail AbstractImage.
# Required for Wagtail search/index and update_index; custom image tables
# don't get wagtailimages migrations, so we add the column here.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0042_privacypage_content_streamfield"),
    ]

    operations = [
        migrations.AddField(
            model_name="lampstandsimage",
            name="file_hash",
            field=models.CharField(
                blank=True,
                db_index=True,
                editable=False,
                max_length=40,
                default="",
            ),
            preserve_default=True,
        ),
    ]
