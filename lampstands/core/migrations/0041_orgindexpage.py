# Migration: re-add OrgIndexPage so legacy "Organizations Listing" pages
# (content_type lampstands.orgindexpage) can be edited or deleted in the admin.

import django.db.models.deletion
from django.db import migrations, models


def backfill_orgindexpage_rows(apps, schema_editor):
    ContentType = apps.get_model("contenttypes", "ContentType")
    Page = apps.get_model("wagtailcore", "Page")
    OrgIndexPage = apps.get_model("lampstands", "OrgIndexPage")

    ct = ContentType.objects.filter(app_label="lampstands", model="orgindexpage").first()
    if not ct:
        return

    for page in Page.objects.filter(content_type=ct):
        if not OrgIndexPage.objects.filter(pk=page.pk).exists():
            OrgIndexPage.objects.create(page_ptr_id=page.pk, intro="")


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0040_contactformfield_churchentryformfield_clean_name"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrgIndexPage",
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
            ],
            options={
                "verbose_name": "Organizations listing",
                "abstract": False,
            },
            bases=("wagtailcore.page",),
        ),
        migrations.RunPython(backfill_orgindexpage_rows, noop),
    ]
