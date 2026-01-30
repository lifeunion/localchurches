"""
Ensure the site root is a Homepage so admins can edit home page content in Wagtail.

If the current site root is a generic Page (not HomePage), you won't see Homepage
fields (disclaimer, info bar, body HTML, etc.). This command either:
- Finds an existing Homepage under the root and sets it as the site root, or
- Creates a new Homepage as a child of the current root and sets it as the site root.

The homepage template (home_page.html) already pulls content from other pages:
- FAQ section: first 4 items from the FAQ index page (slug 'faq')
- Contact form: same form as the Contact page (slug 'contact')
- Testimonies tag line: from Homepage.blogs_tag_line

Run after deploy or when the root page is not a Homepage:
  python manage.py ensure_homepage
"""
from django.core.management.base import BaseCommand
from django.db import transaction


def ensure_homepage(silent=False):
    """
    Ensure the default site's root is a Homepage. Idempotent.
    Returns (success: bool, message: str).
    """
    from wagtail.models import Site, Page
    from lampstands.core.models import HomePage

    site = Site.objects.filter(is_default_site=True).first() or Site.objects.first()
    if not site:
        return False, "No Wagtail site found. Create one in Admin → Settings → Sites."
    if not site.root_page_id:
        return False, "Site has no root page set. Set a root in Admin → Settings → Sites."

    root_page = Page.objects.get(pk=site.root_page_id)
    # Root is already a Homepage
    if root_page.content_type.app_label == "lampstands" and root_page.content_type.model == "homepage":
        return True, "Site root is already a Homepage. Edit it in Pages to change home content."

    # Look for an existing Homepage that is a direct child of root
    existing = HomePage.objects.child_of(root_page).order_by("path").first()
    if existing:
        with transaction.atomic():
            site.root_page_id = existing.pk
            site.save(update_fields=["root_page_id"])
        return True, f"Set site root to existing Homepage '{existing.title}' (ID: {existing.pk}). Edit it in Pages."

    # Create a new Homepage as child of root
    slug = "home"
    if root_page.get_children().filter(slug=slug).exists():
        slug = "homepage"
    if root_page.get_children().filter(slug=slug).exists():
        slug = "home-1"

    home_page = HomePage(
        title="Home",
        slug=slug,
        live=False,
    )
    try:
        with transaction.atomic():
            root_page.add_child(instance=home_page)
            rev = home_page.save_revision()
            rev.publish()
        site.root_page_id = home_page.pk
        site.save(update_fields=["root_page_id"])
        return True, f"Created Homepage '{home_page.title}' and set as site root. Edit it in Pages (ID: {home_page.pk})."
    except Exception as e:
        return False, f"Failed to create Homepage: {e}"


class Command(BaseCommand):
    help = "Ensure the site root is a Homepage so you can edit home content in Wagtail Admin → Pages."

    def handle(self, *args, **options):
        success, message = ensure_homepage(silent=True)
        if success:
            self.stdout.write(self.style.SUCCESS(message))
        else:
            self.stderr.write(self.style.ERROR(message))
