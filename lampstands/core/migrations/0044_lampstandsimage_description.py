# Migration: add description to LampstandsImage to match Wagtail AbstractImage.
# Custom image tables don't get wagtailimages migrations.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0043_lampstandsimage_file_hash"),
    ]

    operations = [
        migrations.AddField(
            model_name="lampstandsimage",
            name="description",
            field=models.CharField(
                blank=True,
                default="",
                max_length=255,
                verbose_name="description",
            ),
            preserve_default=True,
        ),
    ]
