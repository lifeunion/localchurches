"""
Ensure a Wagtail Site exists for the given hostname.

When the app runs on a different domain (e.g. localchurches.onrender.com) than
the existing Site (e.g. www.localchurches.org), links and redirects that use
the Site's hostname can point to the wrong domain. This command creates a
Site for the current hostname so request.site matches the actual request.

Usage:
  python manage.py ensure_site --hostname=localchurches.onrender.com
  SITE_HOSTNAME=localchurches.onrender.com python manage.py ensure_site

Reads hostname from --hostname, or SITE_HOSTNAME, or WAGTAIL_SITE_HOSTNAME.
If a Site with that hostname already exists, does nothing.
"""
import os

from django.core.management.base import BaseCommand

from wagtail.models import Site


class Command(BaseCommand):
    help = 'Ensure a Wagtail Site exists for the given hostname (SITE_HOSTNAME / WAGTAIL_SITE_HOSTNAME)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hostname',
            type=str,
            default=None,
            help='Hostname for the new Site (e.g. localchurches.onrender.com)',
        )

    def handle(self, *args, **options):
        hostname = (
            options.get('hostname')
            or os.environ.get('SITE_HOSTNAME')
            or os.environ.get('WAGTAIL_SITE_HOSTNAME')
        )
        if not hostname:
            self.stdout.write(
                'No hostname (--hostname or SITE_HOSTNAME or WAGTAIL_SITE_HOSTNAME). Skipping.'
            )
            return

        if Site.objects.filter(hostname=hostname).exists():
            self.stdout.write(self.style.SUCCESS(f'Site already exists for {hostname}.'))
            return

        ref = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
        if not ref:
            self.stderr.write(
                'No existing Site found. Create one in Wagtail Admin → Settings → Sites.'
            )
            return

        Site.objects.create(
            hostname=hostname,
            port=ref.port,
            root_page=ref.root_page,
            is_default_site=False,
        )
        self.stdout.write(
            self.style.SUCCESS(f'Created Site for {hostname} (root_page={ref.root_page_id}).')
        )
