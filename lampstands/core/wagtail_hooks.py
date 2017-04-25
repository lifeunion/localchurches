from django.utils.html import format_html_join, format_html
from django.conf import settings

from wagtail.wagtailcore import hooks
from wagtail.wagtailcore.whitelist import allow_without_attributes

from wagtail.contrib.modeladmin.options import ModelAdminGroup, ModelAdmin, modeladmin_register

from .models import ChurchPage


@hooks.register('construct_whitelister_element_rules')
def whitelister_element_rules():
    return {
        'blockquote': allow_without_attributes,
        'span': allow_without_attributes
    }


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        'lampstands/js/hallo-plugins/span.js'
    ]
    js_includes = format_html_join(
        '\n', '<script src="{0}{1}"></script>',
        ((settings.STATIC_URL, filename) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
          registerHalloPlugin('spanbutton');
        </script>
        """
    )

class ChurchAdmin(ModelAdmin):
    model = ChurchPage
    menu_label = 'Localities'
    menu_icon = 'folder-open-inverse'
    menu_order = 200

modeladmin_register(ChurchAdmin)

@hooks.register('insert_global_admin_css')
def import_fontawesome_stylesheet():
    elem = '<link rel="stylesheet" href="{}lampstands/vendor/fontawesome/css/font-awesome.min.css">'.format(
        settings.STATIC_URL
    )
    return format_html(elem)

@hooks.register('before_serve_page')
def change_geodef(page, request, serve_args, serve_kwargs):
    print ("Request:")
    print (request)