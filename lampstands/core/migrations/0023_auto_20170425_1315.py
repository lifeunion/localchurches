# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-25 18:15
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields
import wagtail.wagtailcore.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailsearchpromotions', '0002_capitalizeverbose'),
        ('wagtailforms', '0003_capitalizeverbose'),
        ('wagtailmenus', '0021_auto_20170106_2352'),
        ('wagtailcore', '0032_add_bulk_delete_page_permission'),
        ('wagtailredirects', '0005_capitalizeverbose'),
        ('lampstands', '0022_remove_churchpage_locality_city'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChurchEntryFormPage',
            fields=[
                ('page_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='wagtailcore.Page')),
                ('formatted_title', models.CharField(blank=True, help_text='This is the title displayed on the page, not the document title tag. HTML is permitted. Be careful.', max_length=255)),
                ('intro', wagtail.wagtailcore.fields.RichTextField()),
                ('call_to_action_text', models.CharField(help_text='Displayed above the email submission form.', max_length=255)),
                ('form_button_text', models.CharField(max_length=255)),
                ('thank_you_text', models.CharField(help_text='Displayed on successful form submission.', max_length=255)),
                ('call_to_action_image', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='lampstands.LampstandsImage')),
            ],
            options={
                'abstract': False,
            },
            bases=('wagtailcore.page',),
        ),
        migrations.RenameModel(
            old_name='SignUpFormPageBullet',
            new_name='ChurchEntryFormPageBullet',
        ),
        migrations.RemoveField(
            model_name='signupformpage',
            name='call_to_action_image',
        ),
        migrations.RemoveField(
            model_name='signupformpage',
            name='email_attachment',
        ),
        migrations.RemoveField(
            model_name='signupformpage',
            name='page_ptr',
        ),
        migrations.RemoveField(
            model_name='signupformpagelogo',
            name='logo',
        ),
        migrations.RemoveField(
            model_name='signupformpagelogo',
            name='page',
        ),
        migrations.RemoveField(
            model_name='signupformpagequote',
            name='page',
        ),
        migrations.DeleteModel(
            name='SignUpFormPageResponse',
        ),
        migrations.AlterField(
            model_name='churchentryformpagebullet',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='bullet_points', to='lampstands.ChurchEntryFormPage'),
        ),
        migrations.DeleteModel(
            name='SignUpFormPage',
        ),
        migrations.DeleteModel(
            name='SignUpFormPageLogo',
        ),
        migrations.DeleteModel(
            name='SignUpFormPageQuote',
        ),
    ]
