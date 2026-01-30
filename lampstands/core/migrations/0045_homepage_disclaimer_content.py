# Migration: add disclaimer_content to HomePage for editable disclaimer bar.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0044_lampstandsimage_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="disclaimer_content",
            field=models.TextField(
                blank=True,
                help_text="Disclaimer text shown in the first info bar (after hero). Leave blank for default.",
            ),
        ),
    ]
