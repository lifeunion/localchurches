# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-05-04 22:10
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0030_auto_20170504_1518'),
    ]

    operations = [
        migrations.AlterField(
            model_name='churchpage',
            name='locality_email',
            field=models.EmailField(blank=True, default='Unavailable', max_length=254),
        ),
    ]
