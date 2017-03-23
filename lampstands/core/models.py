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
from wagtail.wagtailforms.models import AbstractEmailForm, AbstractFormField
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
        FieldPanel('blogs_tag_line')
    ]

    @property
    def blog_posts(self):
        # Get list of blog pages.
        blog_posts = BlogPage.objects.live().public()
        return blog_posts


# Standard page

class StandardPageContentBlock(Orderable, ContentBlock):
    page = ParentalKey('lampstands.StandardPage', related_name='content_block')


class StandardPageRelatedLink(Orderable, RelatedLink):
    page = ParentalKey('lampstands.StandardPage', related_name='related_links')


class StandardPageClient(Orderable, RelatedLink):
    page = ParentalKey('lampstands.StandardPage', related_name='clients')
    image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = RelatedLink.panels + [
        ImageChooserPanel('image')
    ]


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

# About page
class AboutPageRelatedLinkButton(Orderable, RelatedLink):
    page = ParentalKey('lampstands.AboutPage', related_name='related_link_buttons')


class AboutPageOffice(Orderable):
    page = ParentalKey('lampstands.AboutPage', related_name='offices')
    title = models.TextField()
    svg = models.TextField(null=True)
    description = models.TextField()

    panels = [
        FieldPanel('title'),
        FieldPanel('description'),
        FieldPanel('svg')
    ]


class AboutPageContentBlock(Orderable):
    page = ParentalKey('lampstands.AboutPage', related_name='content_blocks')
    year = models.IntegerField()
    title = models.TextField()
    description = models.TextField()
    image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        FieldPanel('year'),
        FieldPanel('title'),
        FieldPanel('description'),
        ImageChooserPanel('image')
    ]


class AboutPage(Page):
    main_image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    heading = models.TextField(blank=True)
    intro = models.TextField(blank=True)
    involvement_title = models.TextField(blank=True)

    content_panels = [
        FieldPanel('title', classname='full title'),
        ImageChooserPanel('main_image'),
        FieldPanel('heading', classname='full'),
        FieldPanel('intro', classname='full'),
        InlinePanel('related_link_buttons', label='Header buttons'),
        InlinePanel('content_blocks', label='Content blocks'),
        InlinePanel('offices', label='Offices'),
        FieldPanel('involvement_title'),
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
        per_page = 12
        page = request.GET.get('page')
        paginator = Paginator(blog_posts, per_page)  # Show 10 blog_posts per page
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
    colour = models.CharField(
        "Listing card colour if left blank will display image",
        choices=(
            ('orange', "Orange"),
            ('blue', "Blue"),
            ('white', "White")
        ),
        max_length=255,
        blank=True
    )
    streamfield = StreamField([
        ('firstparagraph', blocks.RichTextBlock()),
        ('story', StoryBlock()),
        ], help_text="Always starts with the second letter after dropcap letter")
    letterdropcap = models.CharField(max_length=1, blank=True)
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
        FieldPanel('colour'),
        FieldPanel('author'),
        FieldPanel('from_area'),
        FieldPanel('letterdropcap'),
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
        # Get list of blog pages that are descendants of this page
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
        per_page = 4
        page = request.GET.get('page')
        paginator = Paginator(beliefs_posts, per_page)  # Show 10 blog_posts per page
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
    letterdropcap = models.CharField(max_length=1, blank=True)
    streamfield = StreamField([
        ('firstparagraph', blocks.RichTextBlock()),
        ('story', StoryBlock()),
        ], help_text="Always starts with the second letter after dropcap letter")
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
        FieldPanel('letterdropcap'),
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
            return render(request, "lampstands/includes/church_listing.html", {
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
    locality_phone_number = models.CharField(validators=[phone_regex], blank=True, max_length=16) # validators should be a list
    locality_email = models.EmailField(blank=True)
    locality_web = models.TextField(validators=[URLValidator()], blank=True)
    last_update = models.DateField(null=True, blank=True)
    
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

class MapPage(Page):
    last_update = models.DateField(null=True, blank=True)

MapPage.content_panels = [
    FieldPanel('title', classname="full title"),
    FieldPanel('last_update'),
]


class TurnkeyApplication(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=255)
    email = models.EmailField()

    class Meta:
        ordering = ['-date']


class TurnkeyApplicationForm(forms.ModelForm):
    class Meta:
        model = TurnkeyApplication
        fields = [
            'name', 'email'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': "Your charity's name"}),
            'email': forms.TextInput(attrs={'placeholder': "Your email address"})
        }


class TurnkeyPageEventsManaged(models.Model):
    page = ParentalKey('lampstands.TurnkeyPage', related_name="events_managed")
    image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        ImageChooserPanel('image')
    ]


class TurnkeyPageQuote(Orderable):
    page = ParentalKey('lampstands.TurnkeyPage', related_name="quotes")
    text = models.TextField()
    person_name = models.CharField(max_length=255)
    organisation_name = models.CharField(max_length=255)

    panels = [
        FieldPanel('text'),
        FieldPanel('person_name'),
        FieldPanel('organisation_name'),
    ]


class TurnkeyAccreditations(Orderable):
    page = ParentalKey('lampstands.TurnkeyPage', related_name="accreditations")
    image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        ImageChooserPanel('image')
    ]


class TurnkeyPage(Page):
    intro = RichTextField()
    form_title = models.CharField(max_length=255)
    form_subtitle = models.CharField(max_length=255)
    form_button_text = models.CharField(max_length=255)
    to_address = models.EmailField(
        verbose_name='to address', blank=True,
        help_text="Optional - form submissions will be emailed to this address"
    )
    body = RichTextField()
    events_managed_title = models.CharField(max_length=255)
    call_to_action_title = models.CharField(max_length=255, blank=True)
    call_to_action_embed_url = models.URLField(blank=True)

    search_fields = Page.search_fields + [
        index.SearchField('intro'),
        index.SearchField('body')
    ]

    def get_context(self, request):
        form = TurnkeyApplicationForm()
        context = super(TurnkeyPage, self).get_context(request)
        context['form'] = form
        return context

    def serve(self, request, *args, **kwargs):
        if request.is_ajax() and request.method == "POST":
            form = TurnkeyApplicationForm(request.POST)
            if form.is_valid():
                form.save()

                if self.to_address:
                    subject = "{} form submission".format(self.title)
                    content = '\n'.join([x[1].label + ': ' + str(form.data.get(x[0])) for x in form.fields.items()])
                    send_mail(subject, content, [self.to_address],)
                return render(
                    request,
                    'lampstands/includes/turnkey_application_landing.html',
                    {'self': self, 'form': form}
                )
            else:
                return render(
                    request,
                    'lampstands/includes/turnkey_application_form.html',
                    {'self': self, 'form': form}
                )
        else:
            return super(TurnkeyPage, self).serve(request)

    content_panels = Page.content_panels + [
        FieldPanel('intro', classname='full'),
        FieldPanel('body', classname='full'),
        MultiFieldPanel([
            FieldPanel('form_title'),
            FieldPanel('form_subtitle'),
            FieldPanel('form_button_text'),
            FieldPanel('to_address'),
        ], "Application Form"),
        MultiFieldPanel([
            FieldPanel('events_managed_title'),
            InlinePanel('events_managed', label="Events Managed")
        ], "Events Managed Section"),
        InlinePanel('quotes', label="Quotes"),
        MultiFieldPanel([
            FieldPanel('call_to_action_title'),
            FieldPanel('call_to_action_embed_url'),
            InlinePanel('accreditations', label="Accreditations")
        ], "Call To Action")
    ]


# Sign-up for something page
class SignUpFormPageBullet(Orderable):
    page = ParentalKey('lampstands.SignUpFormPage', related_name='bullet_points')
    icon = models.CharField(max_length=100, choices=(
        ('lampstands/includes/svg/bulb-svg.html', 'Light bulb'),
        ('lampstands/includes/svg/pro-svg.html', 'Chart'),
        ('lampstands/includes/svg/tick-svg.html', 'Tick'),
    ))
    title = models.CharField(max_length=100)
    body = models.TextField()

    panels = [
        FieldPanel('icon'),
        FieldPanel('title'),
        FieldPanel('body'),
    ]


class SignUpFormPageLogo(Orderable):
    page = ParentalKey('lampstands.SignUpFormPage', related_name='logos')
    logo = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = [
        ImageChooserPanel('logo'),
    ]


class SignUpFormPageQuote(Orderable):
    page = ParentalKey('lampstands.SignUpFormPage', related_name='quotes')
    quote = models.TextField()
    author = models.CharField(max_length=100)
    organisation = models.CharField(max_length=100)

    panels = [
        FieldPanel('quote'),
        FieldPanel('author'),
        FieldPanel('organisation'),
    ]


class SignUpFormPageResponse(models.Model):
    date = models.DateTimeField(auto_now_add=True)
    email = models.EmailField()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return self.email


class SignUpFormPageForm(forms.ModelForm):
    class Meta:
        model = SignUpFormPageResponse
        fields = [
            'email',
        ]
        widgets = {
            'email': forms.TextInput(attrs={'placeholder': "Enter your email address"}),
        }


class SignUpFormPage(Page):
    formatted_title = models.CharField(
        max_length=255, blank=True,
        help_text="This is the title displayed on the page, not the document "
        "title tag. HTML is permitted. Be careful."
    )
    intro = RichTextField()
    call_to_action_text = models.CharField(
        max_length=255, help_text="Displayed above the email submission form."
    )
    call_to_action_image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    form_button_text = models.CharField(max_length=255)
    thank_you_text = models.CharField(max_length=255,
                                      help_text="Displayed on successful form submission.")
    email_subject = models.CharField(max_length=100, verbose_name='subject')
    email_body = models.TextField(verbose_name='body')
    email_attachment = models.ForeignKey(
        'wagtaildocs.Document',
        null=True,
        related_name='+',
        on_delete=models.SET_NULL,
        verbose_name='attachment',
    )
    email_from_address = models.EmailField(
        verbose_name='from address',
        help_text="Anything ending in @lampstands.com is good.")

    sign_up_form_class = SignUpFormPageForm

    content_panels = [
        MultiFieldPanel([
            FieldPanel('title', classname="title"),
            FieldPanel('formatted_title'),
        ], 'Title'),
        FieldPanel('intro', classname="full"),
        InlinePanel('bullet_points', label="Bullet points"),
        InlinePanel('logos', label="Logos"),
        InlinePanel('quotes', label="Quotes"),
        MultiFieldPanel([
            FieldPanel('call_to_action_text'),
            ImageChooserPanel('call_to_action_image'),
            FieldPanel('form_button_text'),
            FieldPanel('thank_you_text'),
        ], 'Form'),
        MultiFieldPanel([
            FieldPanel('email_subject'),
            FieldPanel('email_body'),
            DocumentChooserPanel('email_attachment'),
            FieldPanel('email_from_address'),
        ], 'Email'),
    ]

    def get_context(self, request, *args, **kwargs):
        context = super(SignUpFormPage, self).get_context(request, *args, **kwargs)
        context['form'] = self.sign_up_form_class()
        return context

    @vary_on_headers('X-Requested-With')
    def serve(self, request, *args, **kwargs):
        if request.is_ajax() and request.method == "POST":
            form = self.sign_up_form_class(request.POST)

            if form.is_valid():
                form.save()
                self.send_email_response(form.cleaned_data['email'])
                return render(
                    request,
                    'lampstands/includes/sign_up_form_page_landing.html',
                    {
                        'page': self,
                        'form': form,
                        'legend': self.call_to_action_text
                     }
                )
            else:
                return render(
                    request,
                    'lampstands/includes/sign_up_form_page_form.html',
                    {
                        'page': self,
                        'form': form,
                        'legend': self.call_to_action_text
                    }
                )
        else:
            return super(SignUpFormPage, self).serve(request)

    def send_email_response(self, to_address):
        email_message = EmailMessage(
            subject=self.email_subject,
            body=self.email_body,
            from_email=self.email_from_address,
            to=[to_address],
        )
        email_message.attach_file(self.email_attachment.file.path)
        email_message.send()


class AbstractBaseMarketingLandingPageRelatedLink(Orderable, RelatedLink):
    email_link = models.EmailField("Email link", blank=True,
                                   help_text="Enter email address only, without 'mailto:'")

    @property
    def link(self):
        if self.link_page:
            return self.link_page.url
        elif self.link_document:
            return self.link_document.url
        elif self.link_external:
            return self.link_external
        else:
            return "mailto:{}".format(self.email_link)

    panels = RelatedLink.panels + [
        FieldPanel('email_link')
    ]

    class Meta:
        abstract = True


class MarketingLandingPageHeaderRelatedLink(AbstractBaseMarketingLandingPageRelatedLink):
    page = ParentalKey('lampstands.MarketingLandingPage', related_name='header_related_links')


class MarketingLandingPageIntroRelatedLink(AbstractBaseMarketingLandingPageRelatedLink):
    page = ParentalKey('lampstands.MarketingLandingPage', related_name='intro_related_links')


class MarketingLandingPagePageClients(Orderable, RelatedLink):
    page = ParentalKey('lampstands.MarketingLandingPage', related_name='clients')
    image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )

    panels = RelatedLink.panels + [
        ImageChooserPanel('image')
    ]


class MarketingLandingPageFeaturedItem(Orderable):
    page = ParentalKey('lampstands.MarketingLandingPage', related_name='featured_items')
    related_page = models.ForeignKey('wagtailcore.Page', related_name='+')

    panels = [
        PageChooserPanel('related_page', ['lampstands.BlogPage', 'lampstands.BeliefsPage'])
    ]


class MarketingLandingPage(Page):
    intro = models.TextField('header text', blank=True)
    hero_video_id = models.IntegerField(blank=True, null=True, help_text="Optional. The numeric ID of a Vimeo video to replace the background image.")
    hero_video_poster_image = models.ForeignKey(
        'lampstands.LampstandsImage',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    intro_subtitle = models.CharField('intro subtitle', max_length=255, blank=True)

    class Meta:
        verbose_name = "Marketing Landing Page"

    content_panels = [
        FieldPanel('title', classname="full title"),
        FieldPanel('intro'),
        FieldPanel('hero_video_id'),
        ImageChooserPanel('hero_video_poster_image'),
        InlinePanel('header_related_links', label="Header related items"),
        FieldPanel('intro_subtitle'),
        InlinePanel('intro_related_links', label="Intro related items"),
        InlinePanel('featured_items', label="Featured Items"),
        InlinePanel('clients', label="Clients"),
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
