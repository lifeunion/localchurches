# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-28 06:00
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0023_auto_20170425_1315'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ChurchEntryFormPage',
            new_name='ChurchEntry',
        ),
        migrations.RemoveField(
            model_name='churchentryformpagebullet',
            name='page',
        ),
        migrations.DeleteModel(
            name='ChurchEntryFormPageBullet',
        ),
    ]
