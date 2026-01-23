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


@hooks.register('insert_global_admin_css')
def fix_admin_login_css():
    """Fix CSS issues on Wagtail admin login page (bird icon size, button overlap)."""
    from django.utils.safestring import mark_safe
    css = """
    <style>
        /* Fix Wagtail login page CSS issues */
        .content-wrapper .logo img,
        .content-wrapper .logo svg {{
            max-width: 60px !important;
            max-height: 60px !important;
            width: auto !important;
            height: auto !important;
        }}
        
        .content-wrapper h1 {{
            font-size: 2em !important;
            margin-bottom: 1em !important;
        }}
        
        @media screen and (min-width: 50em) {{
            .content-wrapper h1 {{
                font-size: 3em !important;
            }}
        }}
        
        .content-wrapper .button {{
            margin-top: 1em !important;
            clear: both !important;
        }}
        
        .content-wrapper .fields {{
            margin-top: 1em !important;
        }}
    </style>
    """
    return mark_safe(css)


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
