# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-06 21:07
from __future__ import unicode_literals

from django.db import migrations, models
import lampstands.core.models
import wagtail.wagtailcore.blocks
import wagtail.wagtailcore.fields
import wagtail.wagtailembeds.blocks
import wagtail.wagtailimages.blocks


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0013_auto_20170406_1316'),
    ]

    operations = [
        migrations.AddField(
            model_name='faqpage',
            name='question',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AlterField(
            model_name='faqpage',
            name='streamfield',
            field=wagtail.wagtailcore.fields.StreamField((('answer', wagtail.wagtailcore.blocks.StreamBlock((('h2', wagtail.wagtailcore.blocks.CharBlock(classname='title', icon='title')), ('h3', wagtail.wagtailcore.blocks.CharBlock(classname='title', icon='title')), ('h4', wagtail.wagtailcore.blocks.CharBlock(classname='title', icon='title')), ('intro', wagtail.wagtailcore.blocks.RichTextBlock(icon='pilcrow')), ('paragraph', wagtail.wagtailcore.blocks.RichTextBlock(icon='pilcrow')), ('aligned_image', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('alignment', lampstands.core.models.ImageFormatChoiceBlock()), ('caption', wagtail.wagtailcore.blocks.CharBlock()), ('attribution', wagtail.wagtailcore.blocks.CharBlock(required=False))), label='Aligned image')), ('wide_image', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()),), label='Wide image')), ('bustout', wagtail.wagtailcore.blocks.StructBlock((('image', wagtail.wagtailimages.blocks.ImageChooserBlock()), ('text', wagtail.wagtailcore.blocks.RichTextBlock())))), ('pullquote', wagtail.wagtailcore.blocks.StructBlock((('quote', wagtail.wagtailcore.blocks.CharBlock(classname='quote title')), ('attribution', wagtail.wagtailcore.blocks.CharBlock())))), ('raw_html', wagtail.wagtailcore.blocks.RawHTMLBlock(icon='code', label='Raw HTML')), ('embed', wagtail.wagtailembeds.blocks.EmbedBlock(icon='code'))))),), help_text='Question and answer are to appear in same block'),
        ),
    ]
