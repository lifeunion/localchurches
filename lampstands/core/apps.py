from django.apps import AppConfig


def _patched_page_get_lock(self):
    """Return None when page has no pk (unsaved), avoiding WorkflowState query with object_id='None'."""
    if self.pk is None:
        return None
    return _patched_page_get_lock._original(self)


class LocalChurchesCoreConfig(AppConfig):
    name = 'lampstands.core'
    label = 'lampstands'
    verbose_name = "Local Churches"

    def ready(self):
        from wagtail.models import Page
        _patched_page_get_lock._original = Page.get_lock
        Page.get_lock = _patched_page_get_lock