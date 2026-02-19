# Migration: allow ChurchPage.locality_country to be blank so admins can create
# a new church page without selecting a country first (fixes "cannot create" in Wagtail).

from django.db import migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0047_ensure_homepage_as_site_root"),
    ]

    operations = [
        migrations.AlterField(
            model_name="churchpage",
            name="locality_country",
            field=django_countries.fields.CountryField(
                blank=True,
                blank_label="(select country)",
                max_length=95,
                null=True,
            ),
        ),
    ]
