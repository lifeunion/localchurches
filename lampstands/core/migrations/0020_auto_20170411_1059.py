# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-11 15:59
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0019_auto_20170411_1042'),
    ]

    operations = [
        migrations.AddField(
            model_name='mappage',
            name='google_key_js',
            field=models.TextField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='mappage',
            name='google_url_js',
            field=models.TextField(blank=True, max_length=50),
        ),
    ]
