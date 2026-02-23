# Migration: allow longer position string for wagtail-geo-widget GEOSGeometry format

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0053_churchpage_locality_fax_optional"),
    ]

    operations = [
        migrations.AlterField(
            model_name="churchpage",
            name="position",
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
