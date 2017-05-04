from __future__ import unicode_literals

from django import forms
from django.core.mail import EmailMessage
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.shortcuts import render
from django.utils.functional import cached_property
from django.views.decorators.vary import vary_on_headers

from modelcluster.fields import ParentalKey
from wagtail.contrib.settings.models import BaseSetting, register_setting
from wagtail.wagtailadmin.edit_handlers import (FieldPanel, InlinePanel,
                                                MultiFieldPanel,
                                                PageChooserPanel,
                                                StreamFieldPanel)
from wagtail.wagtailcore import blocks
from wagtail.wagtailadmin.utils import send_mail
from wagtail.wagtailcore.blocks import (CharBlock, FieldBlock, ListBlock,
                                        PageChooserBlock, RawHTMLBlock,
                                        RichTextBlock, StreamBlock,
                                        StructBlock, TextBlock, URLBlock)
from wagtail.wagtailcore.fields import RichTextField, StreamField
from wagtail.wagtailcore.models import Orderable, Page
from wagtail.wagtaildocs.edit_handlers import DocumentChooserPanel
from wagtail.wagtailembeds.blocks import EmbedBlock
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField, AbstractForm
from wagtail.wagtailimages.blocks import ImageChooserBlock
from wagtail.wagtailimages.edit_handlers import ImageChooserPanel
from wagtail.wagtailimages.models import (AbstractImage, AbstractRendition,
                                          Image)
from wagtail.wagtailsearch import index
from wagtail.wagtailsnippets.models import register_snippet

from .fields import ColorField

# added for phone numbers
from django.core.validators import RegexValidator, URLValidator
from django_countries.fields import CountryField

from geoposition.fields import GeopositionField
from urllib.request import urlopen
import json
from django.conf import settings as localitySettings
from django.utils import text

# Streamfield blocks and config

class ImageFormatChoiceBlock(FieldBlock):
    field = forms.ChoiceField(choices=(
        ('left', 'Wrap left'),
        ('right', 'Wrap right'),
        ('half', 'Half width'),
        ('full', 'Full width'),
    ))


class ImageBlock(StructBlock):
    image = ImageChooserBlock()
    alignment = ImageFormatChoiceBlock()
    caption = CharBlock()
    attribution = CharBlock(required=False)

    class Meta:
        icon = "image"


class PhotoGridBlock(StructBlock):
    images = ListBlock(ImageChooserBlock())

    class Meta:
        icon = "grip"


class PullQuoteBlock(StructBlock):
    quote = CharBlock(classname="quote title")
    attribution = CharBlock()

    class Meta:
        icon = "openquote"


class PullQuoteImageBlock(StructBlock):
    quote = CharBlock()
    attribution = CharBlock()
    image = ImageChooserBlock(required=False)


class BustoutBlock(StructBlock):
    image = ImageChooserBlock()
    text = RichTextBlock()

    class Meta:
        icon = "pick"


class WideImage(StructBlock):
    image = ImageChooserBlock()

    class Meta:
        icon = "image"


class StatsBlock(StructBlock):
    pass

    class Meta:
        icon = "order"


class StoryBlock(StreamBlock):
    h2 = CharBlock(icon="title", classname="title")
    h3 = CharBlock(icon="title", classname="title")
    h4 = CharBlock(icon="title", classname="title")
    intro = RichTextBlock(icon="pilcrow")
    paragraph = RichTextBlock(icon="pilcrow")
    aligned_image = ImageBlock(label="Aligned image")
    wide_image = WideImage(label="Wide image")
    bustout = BustoutBlock()
    pullquote = PullQuoteBlock()
    raw_html = RawHTMLBlock(label='Raw HTML', icon="code")
    embed = EmbedBlock(icon="code")

# A couple of abstract classes that contain commonly used fields
class ContentBlock(models.Model):
    content = RichTextField()

    panels = [
        FieldPanel('content'),
    ]

    class Meta:
        abstract = True


class LinkFields(models.Model):
    link_external = models.URLField("External link", blank=True)
    link_page = models.ForeignKey(
        'wagtailcore.Page',
        null=True,
        blank=True,
        related_name='+'
    )
    link_document = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        blank=True,
        related_name='+'
    )

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        else:
            return self.link_external

    panels = [
        FieldPanel('link_external'),
        PageChooserPanel('link_page'),
        DocumentChooserPanel('link_document'),
    ]

    class Meta:
        abstract = True


class ContactFields(models.Model):
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    address_1 = models.CharField(max_length=255, blank=True)
    address_2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    post_code = models.CharField(max_length=10, blank=True)

    panels = [
        FieldPanel('telephone'),
        FieldPanel('email'),
        FieldPanel('address_1'),
        FieldPanel('address_2'),
        FieldPanel('city'),
        FieldPanel('country'),
        FieldPanel('post_code'),
    ]

    class Meta:
        abstract = True


# Carousel items
class CarouselItem(LinkFields):
    image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    embed_url = models.URLField("Embed URL", blank=True)
    caption = models.CharField(max_length=255, blank=True)

    panels = [
        ImageChooserPanel('image'),
        FieldPanel('embed_url'),
        FieldPanel('caption'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Related links
class RelatedLink(LinkFields):
    title = models.CharField(max_length=255, help_text="Link title")

    panels = [
        FieldPanel('title'),
        MultiFieldPanel(LinkFields.panels, "Link"),
    ]

    class Meta:
        abstract = True


# Advert Snippet
class AdvertPlacement(models.Model):
    page = ParentalKey('wagtailcore.Page', related_name='advert_placements')
    advert = models.ForeignKey('lampstands.Advert', related_name='+')


class Advert(models.Model):
    page = models.ForeignKey(
        'wagtailcore.Page',
        related_name='+',
        null=True,
        blank=True
    )
    url = models.URLField(null=True, blank=True)
    text = models.CharField(max_length=255)

    panels = [
        PageChooserPanel('page'),
        FieldPanel('url'),
        FieldPanel('text'),
    ]

    def __str__(self):
        return self.text

register_snippet(Advert)


# Custom image
class LampstandsImage(AbstractImage):
    credit = models.CharField(max_length=255, blank=True)

    admin_form_fields = Image.admin_form_fields + (
        'credit',
    )

    @property
    def credit_text(self):
        return self.credit


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=LampstandsImage)
def image_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


class LampstandsRendition(AbstractRendition):
    image = models.ForeignKey('LampstandsImage', related_name='renditions')

    class Meta:
        unique_together = (
            ('image', 'filter_spec', 'focal_point_key'),
        )


# Receive the pre_delete signal and delete the file associated with the model instance.
@receiver(pre_delete, sender=LampstandsRendition)
def rendition_delete(sender, instance, **kwargs):
    # Pass false so FileField doesn't save the model.
    instance.file.delete(False)


# Home Page

class HomePageHero(Orderable, RelatedLink):
    page = ParentalKey('lampstands.HomePage', related_name='hero')
    colour = models.CharField(max_length=255, help_text="Hex ref colour of link and background gradient, use #23b0b0 for default blue")
    background = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    logo = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    text = models.CharField(
        max_length=255
    )

    panels = RelatedLink.panels + [
        ImageChooserPanel('background'),
        ImageChooserPanel('logo'),
        FieldPanel('colour'),
        FieldPanel('text'),
    ]

class HomePage(Page):
    hero_intro_primary = models.TextField(blank=True)
    hero_intro_secondary = models.TextField(blank=True)
    information_bar_content = models.TextField(blank=True)
    blogs_tag_line = models.TextField(blank=True)
    google_url_js = models.TextField(max_length=50, blank=True)
    google_key_js = models.TextField(max_length=50, blank=True)

    class Meta:
        verbose_name = "Homepage"

    content_panels = [
        FieldPanel('title', classname="full title"),
        MultiFieldPanel(
            [
                FieldPanel('hero_intro_primary'),
                FieldPanel('hero_intro_secondary'),
            ],
            heading="Hero intro"
        ),
        InlinePanel('hero', label="Hero"),
        FieldPanel('information_bar_content'),
        FieldPanel('blogs_tag_line'),
        FieldPanel('google_url_js'),
        FieldPanel('google_key_js'),
    ]

    @property
    def blog_posts(self):
        # Get list of blog pages.
        blog_posts = BlogPage.objects.live().public()
        return blog_posts

# FAQ index page

class FAQIndexPage(Page):
    intro = models.TextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    show_in_play_menu = models.BooleanField(default=False)

    def get_popular_tags(self):
        # Get a ValuesQuerySet of tags ordered by most popular (exclude 'planet-drupal' as this is effectively
        # the same as Drupal and only needed for the rss feed)
        popular_tags = FAQPageTagSelect.objects.all().values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Return first 10 popular tags as tag objects
        # Getting them individually to preserve the order
        return [FAQPageTagList.objects.get(id=tag['tag']) for tag in popular_tags[:10]]

    @property
    def faq_posts(self):
        # Get list of faq pages that are descendants of this page
        # and are not marketing_only
        faq_posts = FAQPage.objects.filter(
            live=True,
            path__startswith=self.path
        )

        return faq_posts

    def serve(self, request):
        # Get faq_posts
        faq_posts = self.faq_posts

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            faq_posts = faq_posts.filter(tags__tag__slug=tag)

        # Pagination
        per_page = 5
        page = request.GET.get('page')
        paginator = Paginator(faq_posts, per_page)  # Show 5 faq_posts per page
        try:
            faq_posts = paginator.page(page)
        except PageNotAnInteger:
            faq_posts = paginator.page(1)
        except EmptyPage:
            faq_posts = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "lampstands/includes/faq_listing.html", {
                'self': self,
                'faq_posts': faq_posts,
                'per_page': per_page,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'faq_posts': faq_posts,
                'per_page': per_page,
            })

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]

# FAQ page
class FAQPageTagList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    def __str__(self):
        return self.name

register_snippet(FAQPageTagList)


class FAQPageTagSelect(Orderable):
    page = ParentalKey('lampstands.FAQPage', related_name='tags')
    tag = models.ForeignKey(
        'lampstands.FAQPageTagList',
        related_name='faq_page_tag_select'
    )

class FAQPage(Page):
    question = models.CharField(max_length=255, blank=True)
    streamfield = StreamField([
        ('answer', StoryBlock()),
        ], help_text="Question and answer are to appear in same block")
    search_fields = Page.search_fields + [
        index.SearchField('streamfield'),
    ]

    @property
    def faq_index(self):
        # Find faq index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific,FAQIndexPage):
                return ancestor

        # No ancestors are blog indexes,
        # just return first blog index in database
        return FAQIndexPage.objects.first()

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('question'),
        StreamFieldPanel('streamfield'),
        InlinePanel('tags', label="Tags")
    ]

# Standard page

class StandardPageContentBlock(Orderable, ContentBlock):
    page = ParentalKey('lampstands.StandardPage', related_name='content_block')

class StandardPage(Page):
    heading = models.CharField(max_length=255, blank=True)
    content = StreamField(StoryBlock())

    show_in_play_menu = models.BooleanField(default=False)

    search_fields = Page.search_fields + [
        index.SearchField('heading'),
        index.SearchField('content'),
    ]

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('heading', classname="full"),
        StreamFieldPanel('content'),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]

# Privacy page
class PrivacyPageContentBlock(Orderable, ContentBlock):
    page = ParentalKey('lampstands.PrivacyPage', related_name='content_block')

class PrivacyPage(Page):
    heading = models.CharField(max_length=255, blank=True)
    content = models.CharField(max_length=255)
    show_in_play_menu = models.BooleanField(default=False)
    search_fields = Page.search_fields + [
        index.SearchField('content'),
    ]
    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('heading'),
        FieldPanel('content'),
    ]
    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]

# About page
class AboutPageContentBlock(Orderable, ContentBlock):
    page = ParentalKey('lampstands.AboutPage', related_name='content_block')

class AboutPage(Page):
    heading = models.CharField(max_length=255, blank=True)
    content = StreamField(StoryBlock())
    show_in_play_menu = models.BooleanField(default=False)
    search_fields = Page.search_fields + [
        index.SearchField('content'),
    ]
    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('heading'),
        StreamFieldPanel('content'),
    ]
    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]

# Services page
class ServicesPageService(Orderable):
    page = ParentalKey('lampstands.ServicesPage', related_name='services')
    title = models.TextField()
    svg = models.TextField(null=True)
    description = models.TextField()
    link = models.ForeignKey(
        'lampstands.ServicePage',
        related_name='+',
        blank=True,
        null=True,
    )

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        PageChooserPanel('link'),
        FieldPanel('svg')
    ]


class ServicesPage(Page):
    main_image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    heading = models.TextField(blank=True)
    intro = models.TextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    content_panels = [
        FieldPanel('title', classname='full title'),
        ImageChooserPanel('main_image'),
        FieldPanel('heading'),
        FieldPanel('intro', classname='full'),
        InlinePanel('services', label='Services'),
    ]


# Service Page

class CaseStudyBlock(StructBlock):
    title = CharBlock(required=True)
    intro = TextBlock(required=True)
    case_studies = ListBlock(StructBlock([
        ('page', PageChooserBlock('lampstands.BeliefsPage')),
        ('title', CharBlock(required=False)),
        ('descriptive_title', CharBlock(required=False)),
        ('image', ImageChooserBlock(required=False)),
    ]))

    class Meta:
        template = 'blocks/case_study_block.html'


class HighlightBlock(StructBlock):
    title = CharBlock(required=True)
    intro = TextBlock(required=False)
    highlights = ListBlock(TextBlock())

    class Meta:
        template = 'blocks/highlight_block.html'


class StepByStepBlock(StructBlock):
    title = CharBlock(required=True)
    intro = TextBlock(required=False)
    steps = ListBlock(StructBlock([
        ('subtitle', CharBlock(required=False)),
        ('title', CharBlock(required=True)),
        ('icon', CharBlock(max_length=9000, required=True, help_text='Paste SVG code here')),
        ('description', TextBlock(required=True))
    ]))

    class Meta:
        template = 'blocks/step_by_step_block.html'


class PeopleBlock(StructBlock):
    title = CharBlock(required=True)
    intro = TextBlock(required=True)
    people = ListBlock(PageChooserBlock())

    class Meta:
        template = 'blocks/people_block.html'


class FeaturedPagesBlock(StructBlock):
    title = CharBlock()
    pages = ListBlock(StructBlock([
        ('page', PageChooserBlock()),
        ('image', ImageChooserBlock()),
        ('text', TextBlock()),
        ('sub_text', CharBlock(max_length=100)),
    ]))

    class Meta:
        template = 'blocks/featured_pages_block.html'


class SignUpFormPageBlock(StructBlock):
    page = PageChooserBlock('lampstands.SignUpFormPage')

    def get_context(self, value):
        context = super(SignUpFormPageBlock, self).get_context(value)
        context['form'] = value['page'].sign_up_form_class()

        return context

    class Meta:
        icon = 'doc-full'
        template = 'blocks/sign_up_form_page_block.html'


class LogosBlock(StructBlock):
    title = CharBlock()
    intro = CharBlock()
    logos = ListBlock(StructBlock((
        ('image', ImageChooserBlock()),
        ('link_page', PageChooserBlock(required=False)),
        ('link_external', URLBlock(required=False)),
    )))

    class Meta:
        icon = 'site'
        template = 'blocks/logos_block.html'

class ServicePageBlock(StreamBlock):
    case_studies = CaseStudyBlock()
    highlights = HighlightBlock()
    pull_quote = PullQuoteBlock(template='blocks/pull_quote_block.html')
    process = StepByStepBlock()
    people = PeopleBlock()
    featured_pages = FeaturedPagesBlock()
    sign_up_form_page = SignUpFormPageBlock()
    logos = LogosBlock()


class ServicePage(Page):
    description = models.TextField()
    streamfield = StreamField(ServicePageBlock())
    particle = models.ForeignKey(
        'ParticleSnippet',
        blank=True,
        null=True,
        on_delete=models.SET_NULL)

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('description', classname="full"),
        StreamFieldPanel('streamfield'),
        FieldPanel('particle'),
    ]


@register_snippet
class ParticleSnippet(models.Model):
    """
    Snippet for configuring particlejs options
    """
    # particle type choices
    CIRCLE = 1
    EDGE = 2
    TRIANGLE = 3
    POLYGON = 4
    STAR = 5
    IMAGE = 6
    PARTICLES_TYPE_CHOICES = (
        (CIRCLE, 'circle'),
        (EDGE, 'edge'),
        (TRIANGLE, 'triangle'),
        (POLYGON, 'polygon'),
        (STAR, 'star'),
        (IMAGE, 'image'),
    )
    # particle movement direction choices
    NONE = 1
    TOP = 2
    TOP_RIGHT = 3
    RIGHT = 4
    BOTTOM_RIGHT = 5
    BOTTOM = 6
    BOTTOM_LEFT = 7
    LEFT = 8
    PARTICLES_MOVE_DIRECTION_CHOICES = (
        (NONE, 'none'),
        (TOP, 'top'),
        (TOP_RIGHT, 'top-right'),
        (RIGHT, 'right'),
        (BOTTOM_RIGHT, 'bottom-right'),
        (BOTTOM, 'bottom'),
        (BOTTOM_LEFT, 'bottom-left'),
        (LEFT, 'left'),
    )
    title = models.CharField(max_length=50)
    number = models.PositiveSmallIntegerField(default=50)
    shape_type = models.PositiveSmallIntegerField(
        choices=PARTICLES_TYPE_CHOICES, default=CIRCLE)
    polygon_sides = models.PositiveSmallIntegerField(default=5)
    size = models.DecimalField(default=2.5, max_digits=4, decimal_places=1)
    size_random = models.BooleanField(default=False)
    colour = ColorField(default='ffffff', help_text="Don't include # symbol.")
    opacity = models.DecimalField(default=0.9, max_digits=2, decimal_places=1)
    opacity_random = models.BooleanField(default=False)
    move_speed = models.DecimalField(
        default=2.5, max_digits=2, decimal_places=1)
    move_direction = models.PositiveSmallIntegerField(
        choices=PARTICLES_MOVE_DIRECTION_CHOICES,
        default=NONE)
    line_linked = models.BooleanField(default=True)
    css_background_colour = ColorField(
        blank=True,
        help_text="Don't include # symbol. Will be overridden by linear gradient")
    css_background_linear_gradient = models.CharField(
        blank=True,
        max_length=255,
        help_text="Enter in the format 'to right, #2b2b2b 0%, #243e3f 28%, #2b2b2b 100%'")
    css_background_url = models.URLField(blank=True, max_length=255)

    def __str__(self):
        return self.title


# blog index page

class BlogIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.BlogIndexPage', related_name='related_links')

class BlogIndexPage(Page):
    intro = models.TextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    show_in_play_menu = models.BooleanField(default=False)

    def get_popular_tags(self):
        # Get a ValuesQuerySet of tags ordered by most popular (exclude 'planet-drupal' as this is effectively
        # the same as Drupal and only needed for the rss feed)
        popular_tags = BlogPageTagSelect.objects.all().values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Return first 10 popular tags as tag objects
        # Getting them individually to preserve the order
        return [BlogPageTagList.objects.get(id=tag['tag']) for tag in popular_tags[:10]]

    @property
    def blog_posts(self):
        # Get list of blog pages that are descendants of this page
        # and are not marketing_only
        blog_posts = BlogPage.objects.filter(
            live=True,
            path__startswith=self.path
        )

        return blog_posts

    def serve(self, request):
        # Get blog_posts
        blog_posts = self.blog_posts

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            blog_posts = blog_posts.filter(tags__tag__slug=tag)

        # Pagination
        per_page = 6
        page = request.GET.get('page')
        paginator = Paginator(blog_posts, per_page)  # Show 6 blog_posts per page
        try:
            blog_posts = paginator.page(page)
        except PageNotAnInteger:
            blog_posts = paginator.page(1)
        except EmptyPage:
            blog_posts = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "lampstands/includes/blog_listing.html", {
                'self': self,
                'blog_posts': blog_posts,
                'per_page': per_page,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'blog_posts': blog_posts,
                'per_page': per_page,
            })

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('related_links', label="Related links"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]


# blog page
class BlogPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.BlogPage', related_name='related_links')


class BlogPageTagList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    def __str__(self):
        return self.name

register_snippet(BlogPageTagList)


class BlogPageTagSelect(Orderable):
    page = ParentalKey('lampstands.BlogPage', related_name='tags')
    tag = models.ForeignKey(
        'lampstands.BlogPageTagList',
        related_name='Blog_page_tag_select'
    )

class BlogPage(Page):
    previewstreamfield = StreamField([
        ('indexpreview', blocks.TextBlock(max_length=400)),
        ], help_text="To show a summarized version in the index page only", blank=True)
    streamfield = StreamField([
        ('wholestory', StoryBlock()),
        ('stats', StatsBlock()),
        ('wideimage', WideImage()),
        ('bustout', BustoutBlock()),
        ('pullimgquote',PullQuoteImageBlock()),
        ('pullquote', PullQuoteBlock()),
        ('photogrid', PhotoGridBlock()),
        ('img', ImageBlock()),
        ('imgchoice', ImageFormatChoiceBlock()),
        ], help_text="Use Raw HTML option if dropcaps etc. are needed to customize look")
    author = models.CharField(max_length=255, blank=True)
    from_area = models.CharField(max_length=255, blank=True)
    canonical_url = models.URLField(blank=True, max_length=255)
    search_fields = Page.search_fields + [
        index.SearchField('streamfield'),
    ]

    @property
    def blog_index(self):
        # Find blog index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific, BlogIndexPage):
                return ancestor

        # No ancestors are blog indexes,
        # just return first blog index in database
        return BlogIndexPage.objects.first()

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('author'),
        FieldPanel('from_area'),
        StreamFieldPanel('previewstreamfield'),
        StreamFieldPanel('streamfield'),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('tags', label="Tags")
    ]

# beliefs index page

class BeliefsIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.BeliefsIndexPage', related_name='related_links')

class BeliefsIndexPage(Page):
    intro = models.TextField(blank=True)
    #content = StreamField(StoryBlock())
    
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    show_in_play_menu = models.BooleanField(default=False)

    def get_popular_tags(self):
        # Get a ValuesQuerySet of tags ordered by most popular (exclude 'planet-drupal' as this is effectively
        # the same as Drupal and only needed for the rss feed)
        popular_tags = BeliefsPageTagSelect.objects.all().values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Return first 10 popular tags as tag objects
        # Getting them individually to preserve the order
        return [BeliefsPageTagList.objects.get(id=tag['tag']) for tag in popular_tags[:10]]

    @property
    def beliefs_posts(self):
        # Get list of beliefs pages that are descendants of this page
        # and are not marketing_only
        beliefs_posts = BeliefsPage.objects.filter(
            live=True,
            path__startswith=self.path
        )

        return beliefs_posts

    def serve(self, request):
        # Get beliefs_posts
        beliefs_posts = self.beliefs_posts

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            beliefs_posts = beliefs_posts.filter(tags__tag__slug=tag)

        # Pagination
        per_page = 9
        page = request.GET.get('page')
        paginator = Paginator(beliefs_posts, per_page)  # Show 8 blog_posts per page
        try:
            beliefs_posts = paginator.page(page)
        except PageNotAnInteger:
            beliefs_posts = paginator.page(1)
        except EmptyPage:
            beliefs_posts = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "lampstands/includes/beliefs_listing.html", {
                'self': self,
                'beliefs_posts': beliefs_posts,
                'per_page': per_page,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'beliefs_posts': beliefs_posts,
                'per_page': per_page,
            })

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('related_links', label="Related links"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]


# beliefs page
class BeliefsPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.BeliefsPage', related_name='related_links')


class BeliefsPageTagList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    def __str__(self):
        return self.name

register_snippet(BeliefsPageTagList)


class BeliefsPageTagSelect(Orderable):
    page = ParentalKey('lampstands.BeliefsPage', related_name='tags')
    tag = models.ForeignKey(
        'lampstands.BeliefsPageTagList',
        related_name='Beliefs_page_tag_select'
    )

class BeliefsPage(Page):
    previewstreamfield = StreamField([
        ('indexpreview', blocks.TextBlock(max_length=300)),
        ], help_text="To show a summarized version in the index page only", blank=True)
    streamfield = StreamField([
        ('wholestory', StoryBlock()),
        ], help_text="Use Raw HTML option if dropcaps etc. are needed to customize look")
    canonical_url = models.URLField(blank=True, max_length=255)
    search_fields = Page.search_fields + [
        index.SearchField('streamfield'),
    ]

    @property
    def beliefs_index(self):
        # Find beliefs index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific, BeliefsIndexPage):
                return ancestor

        # No ancestors are beliefs indexes,
        # just return first beliefs index in database
        return BeliefsIndexPage.objects.first()

    content_panels = [
        FieldPanel('title', classname="full title"),
        StreamFieldPanel('previewstreamfield'),
        StreamFieldPanel('streamfield'),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('tags', label="Tags")
    ]

# Church page
class ChurchIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.ChurchIndexPage', related_name='related_links')

# Church index
class ChurchIndexPage(Page):
    intro = models.TextField(blank=True)
    
    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    def get_popular_tags(self):
        popular_tags = ChurchPageTagSelect.objects.all().values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Return first 10 popular tags as tag objects
        # Getting them individually to preserve the order
        return [ChurchPageTagList.objects.get(id=tag['tag']) for tag in popular_tags[:10]]

    @property
    def church_posts(self):
        # Get list of church pages that are descendants of this page
        church_posts = ChurchPage.objects.filter(
            live=True,
            path__startswith=self.path
        )

        return church_posts

    def serve(self, request):
        # Get church_posts
        church_posts = self.church_posts

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            church_posts = church_posts.filter(tags__tag__slug=tag)

        if request.is_ajax():
            return render(request, "lampstands/includes/localities_listing.html", {
                'self': self,
                'church_posts': church_posts,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'church_posts': church_posts,
            })

    @property
    def churches(self):
        return ChurchPage.objects.live().public()

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('related_links', label="Related links"),
    ]

# Church page
class ChurchPageTagList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    def __str__(self):
        return self.name

register_snippet(ChurchPageTagList)


class ChurchPageTagSelect(Orderable):
    page = ParentalKey('lampstands.ChurchPage', related_name='tags')
    tag = models.ForeignKey(
        'lampstands.ChurchPageTagList',
        related_name='church_page_tag_select'
    )

class ChurchPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.ChurchPage', related_name='related_links')

class ChurchPage(Page):
    locality_name = models.CharField(max_length=255)
    locality_state_or_province = models.CharField(max_length=255, blank=True)
    locality_country = CountryField(blank_label='(select country)')
    short_intro = models.CharField(
        max_length=255, blank=True,
        help_text='A short summary of when the locality started meeting'
    )
    #mailaddr = models.CharField(max_length=255, blank=True, null=True)
    meeting_address = models.CharField(max_length=255, blank=True, null=True)
    position = GeopositionField(blank=True, null=True)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    locality_phone_number = models.CharField(blank=True, max_length=20) # validators should be a list
    locality_email = models.EmailField(blank=True, default="Unavailable")
    #locality_web = models.TextField(validators=[URLValidator()], blank=True, help_text= "Please type: 'http://' in the front of the URL")
    locality_web = models.TextField(blank=True, default="Unavailable", help_text= "Please type: 'http://' in the front of the URL")
    last_update = models.DateField(null=True, blank=True)
    #slug = text.slugify(name_slu)
    
    search_fields = Page.search_fields + [
        index.SearchField('locality_name'),
        index.SearchField('locality_state_or_province'),
        index.SearchField('locality_country'),
        index.SearchField('meeting_address'),
    ]

    @property
    def church_index(self):
        # Find church index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific, ChurchIndexPage):
                return ancestor

        # No ancestors are blog indexes,
        # just return first blog index in database
        return ChurchIndexPage.objects.first()

    def get_latitude_location(self):
        latitude = self.position.latitude
        return str(latitude)

    def get_longitude_location(self):
        longitude = self.position.longitude
        return str(longitude)

    def location(self):
        dictified_loc = dict([ ("latitude", self.get_latitude_location()), ("longitude", self.get_longitude_location())])
        return dictified_loc
        
    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('locality_name'),
        FieldPanel('locality_state_or_province'),
        FieldPanel('locality_country'),
        FieldPanel('short_intro'),
        FieldPanel('meeting_address'),
        FieldPanel('position'),
        FieldPanel('locality_phone_number'),
        FieldPanel('locality_email'),
        FieldPanel('locality_web'),
        FieldPanel('last_update'),
        InlinePanel('tags', label="Tags"),
    ]

# recognition index page

class RecognitionIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.RecognitionIndexPage', related_name='related_links')

class RecognitionIndexPage(Page):
    intro = models.TextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    show_in_play_menu = models.BooleanField(default=False)

    def get_popular_tags(self):
        # Get a ValuesQuerySet of tags ordered by most popular (exclude 'planet-drupal' as this is effectively
        # the same as Drupal and only needed for the rss feed)
        popular_tags = RecognitionPageTagSelect.objects.all().values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Return first 10 popular tags as tag objects
        # Getting them individually to preserve the order
        return [RecognitionPageTagList.objects.get(id=tag['tag']) for tag in popular_tags[:10]]

    @property
    def recognition_posts(self):
        # Get list of blog pages that are descendants of this page
        # and are not marketing_only
        recognition_posts = RecognitionPage.objects.filter(
            live=True,
            path__startswith=self.path
        )

        return recognition_posts

    def serve(self, request):
        # Get blog_posts
        recognition_posts = self.recognition_posts

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            recognition_posts = recognition_posts.filter(tags__tag__slug=tag)

        # Pagination
        per_page = 6
        page = request.GET.get('page')
        paginator = Paginator(recognition_posts, per_page)  # Show 6 blog_posts per page
        try:
            recognition_posts = paginator.page(page)
        except PageNotAnInteger:
            recognition_posts = paginator.page(1)
        except EmptyPage:
            recognition_posts = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "lampstands/includes/recognition_listing.html", {
                'self': self,
                'recognition_posts': recognition_posts,
                'per_page': per_page,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'recognition_posts': recognition_posts,
                'per_page': per_page,
            })

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('related_links', label="Related links"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]


# recognition page
class RecognitionPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.RecognitionPage', related_name='related_links')


class RecognitionPageTagList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    def __str__(self):
        return self.name

register_snippet(RecognitionPageTagList)

class RecognitionPageTagSelect(Orderable):
    page = ParentalKey('lampstands.RecognitionPage', related_name='tags')
    tag = models.ForeignKey(
        'lampstands.RecognitionPageTagList',
        related_name='Recognition_page_tag_select'
    )

class RecognitionPage(Page):
    previewstreamfield = StreamField([
        ('indexpreview', blocks.TextBlock(max_length=400)),
        ], help_text="To show a summarized version in the index page only", blank=True)
    streamfield = StreamField([
        ('wholestory', StoryBlock()),
        ('stats', StatsBlock()),
        ('wideimage', WideImage()),
        ('bustout', BustoutBlock()),
        ('pullimgquote',PullQuoteImageBlock()),
        ('pullquote', PullQuoteBlock()),
        ('photogrid', PhotoGridBlock()),
        ('img', ImageBlock()),
        ('imgchoice', ImageFormatChoiceBlock()),
        ], help_text="Use Raw HTML option if dropcaps etc. are needed to customize look")
    author = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    reference_images = models.ForeignKey('lampstands.LampstandsImage', null=True,
                                   blank=True, on_delete=models.SET_NULL,
                                   related_name='+')
    canonical_url = models.URLField(blank=True, max_length=255)
    search_fields = Page.search_fields + [
        index.SearchField('streamfield'),
    ]

    @property
    def recognition_index(self):
        # Find recognition index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific, RecognitionIndexPage):
                return ancestor

        # No ancestors are recognition indexes,
        # just return first recognition index in database
        return RecognitionIndexPage.objects.first()

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('author'),
        FieldPanel('reference'),
        ImageChooserPanel('reference_images'),
        StreamFieldPanel('previewstreamfield'),
        StreamFieldPanel('streamfield'),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('tags', label="Tags")
    ]

# history index page

class HistoryIndexPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.HistoryIndexPage', related_name='related_links')

class HistoryIndexPage(Page):
    intro = models.TextField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
    ]

    show_in_play_menu = models.BooleanField(default=False)

    def get_popular_tags(self):
        # Get a ValuesQuerySet of tags ordered by most popular (exclude 'planet-drupal' as this is effectively
        # the same as Drupal and only needed for the rss feed)
        popular_tags = HistoryPageTagSelect.objects.all().values('tag').annotate(item_count=models.Count('tag')).order_by('-item_count')

        # Return first 10 popular tags as tag objects
        # Getting them individually to preserve the order
        return [HistoryPageTagList.objects.get(id=tag['tag']) for tag in popular_tags[:10]]

    @property
    def history_posts(self):
        # Get list of history pages that are descendants of this page
        # and are not marketing_only
        history_posts = HistoryPage.objects.filter(
            live=True,
            path__startswith=self.path
        )

        return history_posts

    def serve(self, request):
        # Get history_posts
        history_posts = self.history_posts

        # Filter by tag
        tag = request.GET.get('tag')
        if tag:
            history_posts = history_posts.filter(tags__tag__slug=tag)

        # Pagination
        per_page = 6
        page = request.GET.get('page')
        paginator = Paginator(history_posts, per_page)  # Show 6 blog_posts per page
        try:
            history_posts = paginator.page(page)
        except PageNotAnInteger:
            history_posts = paginator.page(1)
        except EmptyPage:
            history_posts = paginator.page(paginator.num_pages)

        if request.is_ajax():
            return render(request, "lampstands/includes/history_listing.html", {
                'self': self,
                'history_posts': history_posts,
                'per_page': per_page,
            })
        else:
            return render(request, self.template, {
                'self': self,
                'history_posts': history_posts,
                'per_page': per_page,
            })

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('related_links', label="Related links"),
    ]

    promote_panels = [
        MultiFieldPanel(Page.promote_panels, "Common page configuration"),
        FieldPanel('show_in_play_menu'),
    ]

# history page
class HistoryPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.HistoryPage', related_name='related_links')


class HistoryPageTagList(models.Model):
    name = models.CharField(max_length=255)
    slug = models.CharField(max_length=255)

    def __str__(self):
        return self.name

register_snippet(HistoryPageTagList)


class HistoryPageTagSelect(Orderable):
    page = ParentalKey('lampstands.HistoryPage', related_name='tags')
    tag = models.ForeignKey(
        'lampstands.HistoryPageTagList',
        related_name='History_page_tag_select'
    )

class HistoryPage(Page):
    previewstreamfield = StreamField([
        ('indexpreview', blocks.TextBlock(max_length=400)),
        ], help_text="To show a summarized version in the index page only", blank=True)
    streamfield = StreamField([
        ('wholestory', StoryBlock()),
        ('stats', StatsBlock()),
        ('wideimage', WideImage()),
        ('bustout', BustoutBlock()),
        ('pullimgquote',PullQuoteImageBlock()),
        ('pullquote', PullQuoteBlock()),
        ('photogrid', PhotoGridBlock()),
        ('img', ImageBlock()),
        ('imgchoice', ImageFormatChoiceBlock()),
        ], help_text="Use Raw HTML option if dropcaps etc. are needed to customize look")
    main_category = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    reference_images = models.ForeignKey('lampstands.LampstandsImage', null=True,
                                   blank=True, on_delete=models.SET_NULL,
                                   related_name='+')
    canonical_url = models.URLField(blank=True, max_length=255)
    search_fields = Page.search_fields + [
        index.SearchField('streamfield'),
    ]

    @property
    def history_index(self):
        # Find history index in ancestors
        for ancestor in reversed(self.get_ancestors()):
            if isinstance(ancestor.specific, HistoryIndexPage):
                return ancestor

        # No ancestors are history indexes,
        # just return first history index in database
        return HistoryIndexPage.objects.first()

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('main_category'),
        FieldPanel('reference'),
        ImageChooserPanel('reference_images'),
        StreamFieldPanel('previewstreamfield'),
        StreamFieldPanel('streamfield'),
        InlinePanel('related_links', label="Related links"),
        InlinePanel('tags', label="Tags")
    ]


class MapPage(Page):
    last_update = models.DateField(null=True, blank=True)
    google_url_js = models.TextField(max_length=50, blank=True)
    google_key_js = models.TextField(max_length=50, blank=True)

    @property
    def get_locality_json(self):
        json_locality_url = 'https://safe-cove-64619.herokuapp.com/api-localities/?format=json'
        return json_locality_url

    def geoinfo_lat(self):
        geoinfo_lat = '0' 
        return geoinfo_lat

    def geoinfo_lng(self):
        geoinfo_lng = '0' 
        return geoinfo_lng

    def zoom_deflevel(self):
        zoom_deflevel = 12 
        return zoom_deflevel

    def serve(self, request):
        # Filter by tag
        geoinfo_lat = request.GET.get('lat')
        geoinfo_lng = request.GET.get('lng')
        zoom_deflevel = 7

        print (geoinfo_lat)
        print (geoinfo_lng)

        if not geoinfo_lat:
            print ('execute default:')
            geoinfo_lat = '36.7783'
            zoom_deflevel = 4

        if not geoinfo_lng:
            geoinfo_lng = '-119.4179'
            zoom_deflevel = 4

        return render(request, self.template, {
                'self': self,
                'geoinfo_lat': geoinfo_lat,
                'geoinfo_lng': geoinfo_lng,
                'zoom_deflevel': zoom_deflevel
            })

MapPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('last_update'),
    FieldPanel('google_url_js'),
    FieldPanel('google_key_js')
]

# ChurchEntry page
class ChurchentryFormField(AbstractFormField):
    page = ParentalKey('Churchentry', related_name='form_fields')

class ChurchentryLandingPageRelatedLinkButton(Orderable, RelatedLink):
    page = ParentalKey('lampstands.Churchentry', related_name='related_link_buttons')

class Churchentry(AbstractForm):
    intro = RichTextField(blank=True)
    thank_you_text = models.CharField(max_length=255, help_text='e.g. Thanks!')
    thank_you_follow_up = models.CharField(max_length=255, help_text='e.g. We\'ll be in touch')
    landing_page_button_title = models.CharField(max_length=255, blank=True)
    landing_page_button_link = models.ForeignKey(
        'wagtailcore.Page', null=True, blank=True, related_name='+',
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Churchentry Page"

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        InlinePanel('form_fields', label="Form fields"),
        MultiFieldPanel([
            FieldPanel('thank_you_text'),
            FieldPanel('thank_you_follow_up'),
            PageChooserPanel('landing_page_button_link'),
            FieldPanel('landing_page_button_title'),
        ], "Landing page"),
    ]

# Contact page
class ContactFormField(AbstractFormField):
    page = ParentalKey('Contact', related_name='form_fields')

class ContactLandingPageRelatedLinkButton(Orderable, RelatedLink):
    page = ParentalKey('lampstands.Contact', related_name='related_link_buttons')

class Contact(AbstractEmailForm):
    intro = RichTextField(blank=True)
    main_image = models.ForeignKey('lampstands.LampstandsImage', null=True,
                                   blank=True, on_delete=models.SET_NULL,
                                   related_name='+')
    landing_image = models.ForeignKey('lampstands.LampstandsImage', null=True,
                                      blank=True, on_delete=models.SET_NULL,
                                      related_name='+')
    thank_you_text = models.CharField(max_length=255, help_text='e.g. Thanks!')
    thank_you_follow_up = models.CharField(max_length=255, help_text='e.g. We\'ll be in touch')
    landing_page_button_title = models.CharField(max_length=255, blank=True)
    landing_page_button_link = models.ForeignKey(
        'wagtailcore.Page', null=True, blank=True, related_name='+',
        on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = "Contact Page"

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro', classname="full"),
        ImageChooserPanel('main_image'),
        InlinePanel('form_fields', label="Form fields"),
        MultiFieldPanel([
            FieldPanel('to_address', classname="full"),
            FieldPanel('from_address', classname="full"),
            FieldPanel('subject', classname="full"),
        ], "Email"),
        MultiFieldPanel([
            ImageChooserPanel('landing_image'),
            FieldPanel('thank_you_text'),
            FieldPanel('thank_you_follow_up'),
            PageChooserPanel('landing_page_button_link'),
            FieldPanel('landing_page_button_title'),
        ], "Landing page"),
    ]

@register_setting
class GlobalSettings(BaseSetting):

    contact_telephone = models.CharField(max_length=255, help_text='Telephone')
    contact_email = models.EmailField(max_length=255, help_text='Email address')
    contact_twitter = models.CharField(max_length=255, help_text='Twitter')
    email_newsletter_teaser = models.CharField(max_length=255, help_text='Text that sits above the email newsletter')
    oxford_address_title = models.CharField(max_length=255, help_text='Full address')
    oxford_address = models.CharField(max_length=255, help_text='Full address')
    oxford_address_link = models.URLField(max_length=255, help_text='Link to google maps')
    oxford_address_svg = models.CharField(max_length=9000, help_text='Paste SVG code here')
    bristol_address_title = models.CharField(max_length=255, help_text='Full address')
    bristol_address = models.CharField(max_length=255, help_text='Full address')
    bristol_address_link = models.URLField(max_length=255, help_text='Link to google maps')
    bristol_address_svg = models.CharField(max_length=9000, help_text='Paste SVG code here')
    phili_address_title = models.CharField(max_length=255, help_text='Full address')
    phili_address = models.CharField(max_length=255, help_text='Full address')
    phili_address_link = models.URLField(max_length=255, help_text='Link to google maps')
    phili_address_svg = models.CharField(max_length=9000, help_text='Paste SVG code here')
    contact_widget_intro = models.TextField()
    contact_widget_call_to_action = models.TextField()
    contact_widget_button_text = models.TextField()

    class Meta:
        verbose_name = 'Global Settings'

    panels = [
        FieldPanel('contact_telephone'),
        FieldPanel('contact_email'),
        FieldPanel('contact_twitter'),
        FieldPanel('email_newsletter_teaser'),
        FieldPanel('oxford_address_title'),
        FieldPanel('oxford_address'),
        FieldPanel('oxford_address_link'),
        FieldPanel('oxford_address_svg'),
        FieldPanel('bristol_address_title'),
        FieldPanel('bristol_address'),
        FieldPanel('bristol_address_link'),
        FieldPanel('bristol_address_svg'),
        FieldPanel('phili_address_title'),
        FieldPanel('phili_address'),
        FieldPanel('phili_address_link'),
        FieldPanel('phili_address_svg'),

        MultiFieldPanel([
            PageChooserPanel('contact_person'),
            FieldPanel('contact_widget_intro'),
            FieldPanel('contact_widget_call_to_action'),
            FieldPanel('contact_widget_button_text'),
        ], 'Contact widget')
    ]


class SubMenuItemBlock(StreamBlock):
    subitem = PageChooserBlock()


class MenuItemBlock(StructBlock):
    page = PageChooserBlock()
    subitems = SubMenuItemBlock()

    class Meta:
        template = "lampstands/includes/menu_item.html"


class MenuBlock(StreamBlock):
    items = MenuItemBlock()


@register_setting
class MainMenu(BaseSetting):
    menu = StreamField(MenuBlock(), blank=True)

    panels = [
        StreamFieldPanel('menu'),
    ]
