# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-28 21:15
from __future__ import unicode_literals

from django.db import migrations
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0026_auto_20170428_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='churchentryformfield',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='form_fields', to='lampstands.Churchentry'),
        ),
    ]
