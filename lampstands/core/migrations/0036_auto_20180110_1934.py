# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-01-11 01:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0035_auto_20170508_2341'),
    ]

    operations = [
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_five',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_five_phone',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_four',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_four_phone',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_one',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_one_phone',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_six',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_six_phone',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_three',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_three_phone',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_two',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='churchpage',
            name='locality_contact_brother_two_phone',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
    ]
