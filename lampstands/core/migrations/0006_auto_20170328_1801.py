# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-28 23:01
from __future__ import unicode_literals

from django.db import migrations
import lampstands.core.models
import wagtail.wagtailcore.blocks
import wagtail.wagtailcore.fields
import wagtail.wagtailembeds.blocks
import wagtail.wagtailimages.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0005_auto_20170323_0018'),
    ]

    operations = [
        migrations.AlterField(
            model_name='blogpage',
            name='streamfield',
            field=wagtail.wagtailcore.fields.StreamField((('firstparagraph', wagtail.wagtailcore.blocks.RichTextBlock()), ('story', wagtail.wagtailcore.blocks.StreamBlock((('h2', wagtail.wagtailcore.blocks.CharBlock(classname='title', icon='title')), ('h3', wagtail.wagtailcore.blocks.CharBlock(classname='title', icon='title')), ('h4', wagtail.wagtailcore.blocks.CharBlock(classname='title', icon='title')), ('intro', wagtail.wagtailcore.blocks.RichTextBlock(icon='pilcrow')), ('paragraph', wagtail.wagtailcore.blocks.RichTextBlock(icon='pilcrow')), ('aligned_image', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('alignment', lampstands.core.models.ImageFormatChoiceBlock()), ('caption', wagtail.wagtailcore.blocks.CharBlock()), ('attribution', wagtail.wagtailcore.blocks.CharBlock(required=False))), label='Aligned image')), ('wide_image', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()),), label='Wide image')), ('bustout', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('text', wagtail.wagtailcore.blocks.RichTextBlock())))), ('pullquote', wagtail.wagtailcore.blocks.StructBlock((('quote', wagtail.wagtailcore.blocks.CharBlock(classname='quote title')), ('attribution', wagtail.wagtailcore.blocks.CharBlock())))), ('raw_html', wagtail.wagtailcore.blocks.RawHTMLBlock(icon='code', label='Raw HTML')), ('embed', wagtail.wagtailembeds.blocks.EmbedBlock(icon='code'))))), ('stats', wagtail.wagtailcore.blocks.StructBlock(())), ('wideimage', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()),))), ('bustout', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('text', wagtail.wagtailcore.blocks.RichTextBlock())))), ('pullimgquote', wagtail.wagtailcore.blocks.StructBlock((('quote', wagtail.wagtailcore.blocks.CharBlock()), ('attribution', wagtail.wagtailcore.blocks.CharBlock()), ('image', wagtail.wagtailimages.blocks.ImageChooserBlock(required=False))))), ('pullquote', wagtail.wagtailcore.blocks.StructBlock((('quote', wagtail.wagtailcore.blocks.CharBlock(classname='quote title')), ('attribution', wagtail.wagtailcore.blocks.CharBlock())))), ('photogrid', wagtail.wagtailcore.blocks.StructBlock((('images', wagtail.wagtailcore.blocks.ListBlock(wagtail.wagtailimages.blocks.ImageChooserBlock())),))), ('img', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('alignment', lampstands.core.models.ImageFormatChoiceBlock()), ('caption', wagtail.wagtailcore.blocks.CharBlock()), ('attribution', wagtail.wagtailcore.blocks.CharBlock(required=False))))), ('imgchoice', lampstands.core.models.ImageFormatChoiceBlock())), help_text='Always starts with the second letter after dropcap letter'),
        ),
    ]
