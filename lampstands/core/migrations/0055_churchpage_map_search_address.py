# Migration: add map_search_address for widget-only address (decoupled from meeting_address)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0054_churchpage_position_max_length"),
    ]

    operations = [
        migrations.AddField(
            model_name="churchpage",
            name="map_search_address",
            field=models.CharField(
                blank=True,
                help_text="Used only by the map below to search and place the marker. Does not affect the meeting address above.",
                max_length=255,
                null=True,
            ),
        ),
    ]
