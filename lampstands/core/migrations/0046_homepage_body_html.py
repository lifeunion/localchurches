# Migration: add body_html to HomePage for admin-editable custom HTML below hero.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0045_homepage_disclaimer_content"),
    ]

    operations = [
        migrations.AddField(
            model_name="homepage",
            name="body_html",
            field=models.TextField(
                blank=True,
                help_text="Optional: Custom HTML for the home page content below the hero. Leave blank to use the default layout (disclaimer, testimonies, FAQ, contact). When set, this HTML replaces that default content.",
            ),
        ),
    ]
