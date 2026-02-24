"""
Print regular vs consented brother contact data for a church (by locality name).

Usage:
  python manage.py check_church_contacts Anaheim
  python manage.py check_church_contacts "Fullerton"

On Render: use a one-off job or Shell and run:
  python manage.py check_church_contacts Anaheim
"""
from django.core.management.base import BaseCommand

from lampstands.core.models import ChurchPage


class Command(BaseCommand):
    help = 'Print regular vs consented brother data for church(es) matching a locality name'

    def add_arguments(self, parser):
        parser.add_argument(
            'locality',
            nargs='?',
            default='Anaheim',
            help='Locality name to search (e.g. Anaheim, Fullerton). Default: Anaheim',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Show all matching churches (default: first 5)',
        )

    def handle(self, *args, **options):
        locality = options['locality']
        show_all = options['all']

        pages = ChurchPage.objects.filter(locality_name__icontains=locality)
        if not pages.exists():
            pages = ChurchPage.objects.filter(title__icontains=locality)
        if not pages.exists():
            self.stdout.write(self.style.WARNING(f'No church found for locality "{locality}".'))
            return

        limit = None if show_all else 5
        for p in pages[:limit]:
            self.stdout.write('')
            self.stdout.write(self.style.HTTP_INFO(f'--- Church: {p.title}'))
            self.stdout.write(f'    locality_name: {p.locality_name!r}  slug: {p.slug}')
            self.stdout.write('')

            self.stdout.write('REGULAR (locality_contact_brother_1..4):')
            for i in range(1, 5):
                n = getattr(p, f'locality_contact_brother_{i}', None)
                ph = getattr(p, f'locality_contact_brother_{i}_phone', None)
                self.stdout.write(f'  {i}: name={n!r}  phone={ph!r}')

            self.stdout.write('ADDITIONAL (locality_contact_brother_5..6):')
            for i in range(5, 7):
                n = getattr(p, f'locality_contact_brother_{i}', None)
                ph = getattr(p, f'locality_contact_brother_{i}_phone', None)
                self.stdout.write(f'  {i}: name={n!r}  phone={ph!r}')

            self.stdout.write('')
            self.stdout.write('CONSENTED (consented_brother_1..4):')
            for i in range(1, 5):
                n = getattr(p, f'consented_brother_{i}', None)
                ph = getattr(p, f'consented_brother_{i}_phone', None)
                self.stdout.write(f'  {i}: name={n!r}  phone={ph!r}')
            self.stdout.write('')

        if not show_all and pages.count() > limit:
            self.stdout.write(self.style.NOTICE(f'... and {pages.count() - limit} more. Use --all to show all.'))
