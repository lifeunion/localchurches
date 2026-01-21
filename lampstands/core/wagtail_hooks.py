from django.utils.html import format_html_join, format_html
from django.conf import settings

from wagtail import hooks
from wagtail_modeladmin.options import ModelAdminGroup, ModelAdmin, modeladmin_register

from .models import ChurchPage


# Note: The whitelister_element_rules hook is deprecated in modern Wagtail.
# Rich text now uses Draftail which handles this differently.
# Keeping this for backwards compatibility during migration.


@hooks.register('insert_global_admin_css')
def import_fontawesome_stylesheet():
    elem = '<link rel="stylesheet" href="{}lampstands/vendor/fontawesome/css/font-awesome.min.css">'.format(
        settings.STATIC_URL
    )
    return format_html(elem)


class ChurchAdmin(ModelAdmin):
    model = ChurchPage
    menu_label = 'Localities'
    menu_icon = 'folder-open-inverse'
    menu_order = 200


modeladmin_register(ChurchAdmin)


@hooks.register('before_serve_page')
def change_geodef(page, request, serve_args, serve_kwargs):
    # Hook for page serving - return None to continue normal processing
    return None
