# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-23 04:47
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0003_auto_20170322_2048'),
    ]

    operations = [
        migrations.AddField(
            model_name='beliefspage',
            name='letterdropcap',
            field=models.CharField(blank=True, max_length=1),
        ),
        migrations.AlterField(
            model_name='churchpage',
            name='locality_phone_number',
            field=models.CharField(blank=True, max_length=16),
        ),
    ]
