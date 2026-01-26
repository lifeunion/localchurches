"""
Find and optionally replace wrong domain (e.g. localchurches.org) in CMS text and URL fields.

When the wrong link appears "in the text", it is usually in:
- Contact.intro, Churchentry.intro (rich text)
- GlobalSettings: address links, contact widget text
- canonical_url on pages
- link_external on related links, adverts, etc.
- StreamField body content (report only; edit in Wagtail to fix)

Usage:
  python manage.py find_wrong_domain_links
  python manage.py find_wrong_domain_links --replace
  python manage.py find_wrong_domain_links --old=www.localchurches.org --new=localchurches.onrender.com --replace

By default scans for www.localchurches.org and localchurches.org, replaces with --new.
"""
from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models

try:
    from wagtail.fields import RichTextField, StreamField
except ImportError:
    RichTextField = StreamField = None


# Order matters: replace longer patterns first.
OLD_PATTERNS_DEFAULT = ['www.localchurches.org', 'localchurches.org']
NEW_DEFAULT = 'localchurches.onrender.com'


def _value_to_str(val):
    return str(val or '')


def _replace_all(s, old_patterns, new):
    out = s or ''
    for old in old_patterns:
        out = out.replace(old, new)
    return out


class Command(BaseCommand):
    help = 'Find (and optionally replace) wrong domain in CMS text/URL fields'

    def add_arguments(self, parser):
        parser.add_argument(
            '--old',
            type=str,
            default=','.join(OLD_PATTERNS_DEFAULT),
            help='Comma-separated old domains to find (default: www.localchurches.org,localchurches.org)',
        )
        parser.add_argument(
            '--new',
            type=str,
            default=NEW_DEFAULT,
            help='New domain to replace with',
        )
        parser.add_argument(
            '--replace',
            action='store_true',
            help='Apply replacements and save (default: only report)',
        )

    def handle(self, *args, **options):
        old_patterns = [p.strip() for p in (options.get('old') or '').split(',') if p.strip()]
        if not old_patterns:
            old_patterns = OLD_PATTERNS_DEFAULT
        new_domain = (options.get('new') or NEW_DEFAULT).strip()
        do_replace = options.get('replace', False)

        self.stdout.write(f'Looking for: {old_patterns}')
        self.stdout.write(f'Replace with: {new_domain}')
        self.stdout.write(f'Mode: {"REPLACE and save" if do_replace else "REPORT only"}')
        self.stdout.write('')

        found = []
        replaced = 0

        for model in apps.get_models():
            if getattr(model._meta, 'abstract', True):
                continue
            if not hasattr(model, 'objects'):
                continue

            for f in model._meta.get_fields():
                if not hasattr(f, 'name'):
                    continue
                if getattr(f, 'remote_field', None) and f.remote_field and not getattr(f, 'primary_key', False):
                    continue
                if f.many_to_many:
                    continue

                is_stream = StreamField is not None and isinstance(f, StreamField)
                is_text = isinstance(f, (models.CharField, models.TextField, models.URLField))
                if RichTextField is not None:
                    is_text = is_text or isinstance(f, RichTextField)

                if not (is_text or is_stream):
                    continue

                try:
                    qs = model.objects.all()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'  Skip {model._meta.label}.objects: {e}'))
                    continue

                for obj in qs:
                    try:
                        val = getattr(obj, f.name, None)
                    except Exception:
                        continue
                    s = _value_to_str(val)
                    if not s:
                        continue

                    if not any(p in s for p in old_patterns):
                        continue

                    label = f'{model._meta.label} pk={getattr(obj, "pk", "?")}'
                    if hasattr(obj, 'title'):
                        label += f' title={str(getattr(obj, "title", ""))[:50]}'
                    found.append((model, f.name, obj, s, is_stream))

        # Report
        for model, fname, obj, s, is_stream in found:
            excerpt = (s[:120] + '...') if len(s) > 120 else s
            self.stdout.write(self.style.WARNING(f'  {model._meta.label} pk={getattr(obj,"pk","?")} .{fname}'))
            self.stdout.write(f'    excerpt: {excerpt[:100]}...' if len(excerpt) > 100 else f'    excerpt: {excerpt}')

            if do_replace and not is_stream:
                new_val = _replace_all(s, old_patterns, new_domain)
                if new_val != s:
                    try:
                        setattr(obj, fname, new_val)
                        obj.save()
                        replaced += 1
                        self.stdout.write(self.style.SUCCESS(f'    -> replaced and saved'))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'    -> save failed: {e}'))
            elif do_replace and is_stream:
                self.stdout.write('    -> StreamField: only reported; edit in Wagtail to change.')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Found {len(found)} field(s) containing the old domain.'))
        if do_replace:
            self.stdout.write(self.style.SUCCESS(f'Replaced and saved {replaced} field(s).'))
            if len(found) > replaced:
                self.stdout.write('Remaining: StreamField or save errors; fix in Wagtail.')
