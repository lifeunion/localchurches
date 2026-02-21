from django.apps import AppConfig


def _patched_page_get_lock(self):
    """Return None when page has no pk (unsaved), avoiding WorkflowState query with object_id='None'."""
    if self.pk is None:
        return None
    return _patched_page_get_lock._original(self)


class _SafeWorkflowDescriptor:
    """Descriptor that returns None when instance.pk is None, else delegates to original."""

    def __init__(self, original):
        self._original = original

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if getattr(instance, 'pk', None) is None:
            return None
        return self._original.__get__(instance, owner)


class LocalChurchesCoreConfig(AppConfig):
    name = 'lampstands.core'
    label = 'lampstands'
    verbose_name = "Local Churches"

    def ready(self):
        from wagtail.models import Page

        _patched_page_get_lock._original = Page.get_lock
        Page.get_lock = _patched_page_get_lock

        # Avoid WorkflowState query with object_id='None' when page is unsaved (add form).
        for attr in ('current_workflow_state', 'current_workflow_task_state', 'current_workflow_task'):
            if not hasattr(Page, attr):
                continue
            setattr(Page, attr, _SafeWorkflowDescriptor(getattr(Page, attr)))