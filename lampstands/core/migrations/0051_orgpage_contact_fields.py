# Migration: add contact and address fields to OrgPage (phone, email, address, website, etc.)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0050_orgpage_add_intro_body_if_missing"),
    ]

    operations = [
        migrations.AddField(
            model_name="orgpage",
            name="phone",
            field=models.CharField(blank=True, default="", help_text="Phone number", max_length=50),
        ),
        migrations.AddField(
            model_name="orgpage",
            name="fax",
            field=models.CharField(blank=True, default="", help_text="Fax number", max_length=50),
        ),
        migrations.AddField(
            model_name="orgpage",
            name="email",
            field=models.EmailField(blank=True, default="", help_text="Email address", max_length=254),
        ),
        migrations.AddField(
            model_name="orgpage",
            name="website",
            field=models.URLField(blank=True, default="", help_text="Organization website (include https://)", max_length=255),
        ),
        migrations.AddField(
            model_name="orgpage",
            name="address",
            field=models.TextField(blank=True, default="", help_text="Street address, city, state, postal code"),
        ),
        migrations.AddField(
            model_name="orgpage",
            name="contact_name",
            field=models.CharField(blank=True, default="", help_text="Primary contact person name", max_length=255),
        ),
        migrations.AddField(
            model_name="orgpage",
            name="contact_phone",
            field=models.CharField(blank=True, default="", help_text="Primary contact phone", max_length=50),
        ),
    ]
