# Migration: add OrgPage model with intro/body so legacy org pages can be edited and display content.
# Backfills rows for existing pages that have content_type lampstands.orgpage.

import django.db.models.deletion
from django.db import migrations, models


def backfill_orgpage_rows(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Page = apps.get_model("wagtailcore", "Page")
    OrgPage = apps.get_model("lampstands", "OrgPage")

    ct = ContentType.objects.filter(app_label="lampstands", model="orgpage").first()
    if not ct:
        return

    for page in Page.objects.filter(content_type=ct):
        if not OrgPage.objects.filter(pk=page.pk).exists():
            OrgPage.objects.create(page_ptr_id=page.pk, intro="", body="")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0048_churchpage_locality_country_optional"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrgPage",
            fields=[
                (
                    "page_ptr",
                    models.OneToOneField(
                        auto_created=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        parent_link=True,
                        primary_key=True,
                        serialize=False,
                        to="wagtailcore.page",
                    ),
                ),
                ("intro", models.TextField(blank=True)),
                ("body", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Organization page (legacy)",
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.RunPython(backfill_orgpage_rows, noop),
    ]
