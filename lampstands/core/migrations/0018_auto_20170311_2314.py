# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-12 05:14
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailsearchpromotions', '0002_capitalizeverbose'),
        ('wagtailredirects', '0005_capitalizeverbose'),
        ('wagtailmenus', '0021_auto_20170106_2352'),
        ('wagtaildocs', '0007_merge'),
        ('wagtailforms', '0003_capitalizeverbose'),
        ('wagtailcore', '0032_add_bulk_delete_page_permission'),
        ('lampstands', '0017_auto_20170310_1322'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChurchPageRelatedLink',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('link_external', models.URLField(blank=True, verbose_name='External link')),
                ('title', models.CharField(help_text='Link title', max_length=255)),
                ('link_document', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtaildocs.Document')),
                ('link_page', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.Page')),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_links', to='lampstands.ChurchPage')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ChurchPageTagList',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('slug', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='ChurchPageTagSelect',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('page', modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='tags', to='lampstands.ChurchPage')),
                ('tag', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='church_page_tag_select', to='lampstands.ChurchPageTagList')),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.RemoveField(
            model_name='blogpageauthor',
            name='author',
        ),
        migrations.RemoveField(
            model_name='blogpageauthor',
            name='page',
        ),
        migrations.RemoveField(
            model_name='personindexpage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='personpage',
            name='feed_image',
        ),
        migrations.RemoveField(
            model_name='personpage',
            name='image',
        ),
        migrations.RemoveField(
            model_name='personpage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='personpagerelatedlink',
            name='link_document',
        ),
        migrations.RemoveField(
            model_name='personpagerelatedlink',
            name='link_page',
        ),
        migrations.RemoveField(
            model_name='personpagerelatedlink',
            name='page',
        ),
        migrations.RemoveField(
            model_name='workpageauthor',
            name='author',
        ),
        migrations.RemoveField(
            model_name='workpageauthor',
            name='page',
        ),
        migrations.RemoveField(
            model_name='globalsettings',
            name='contact_person',
        ),
        migrations.RemoveField(
            model_name='workpage',
            name='author_left',
        ),
        migrations.AddField(
            model_name='workpage',
            name='author',
            field=models.CharField(blank=True, help_text='author', max_length=255),
        ),
        migrations.DeleteModel(
            name='BlogPageAuthor',
        ),
        migrations.DeleteModel(
            name='PersonIndexPage',
        ),
        migrations.DeleteModel(
            name='PersonPage',
        ),
        migrations.DeleteModel(
            name='PersonPageRelatedLink',
        ),
        migrations.DeleteModel(
            name='WorkPageAuthor',
        ),
    ]
