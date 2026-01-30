# Migration: ensure the default site root is a Homepage so admins can edit home in Wagtail.
# Runs ensure_homepage logic: if root is not HomePage, create or reuse a Homepage and set as root.

from django.db import migrations


def run_ensure_homepage(apps, schema_editor):
    from lampstands.core.management.commands.ensure_homepage import ensure_homepage
    ensure_homepage(silent=True)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("lampstands", "0046_homepage_body_html"),
    ]

    operations = [
        migrations.RunPython(run_ensure_homepage, noop),
    ]
