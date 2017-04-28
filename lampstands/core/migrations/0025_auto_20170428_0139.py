# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-04-28 06:39
from __future__ import unicode_literals

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import modelcluster.fields


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0024_auto_20170428_0100'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChurchEntryFormPageBullet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sort_order', models.IntegerField(blank=True, editable=False, null=True)),
                ('icon', models.CharField(choices=[('lampstands/includes/svg/bulb-svg.html', 'Light bulb'), ('lampstands/includes/svg/pro-svg.html', 'Chart'), ('lampstands/includes/svg/tick-svg.html', 'Tick')], max_length=100)),
                ('title', models.CharField(max_length=100)),
                ('body', models.TextField()),
            ],
            options={
                'ordering': ['sort_order'],
                'abstract': False,
            },
        ),
        migrations.RenameModel(
            old_name='ChurchEntry',
            new_name='ChurchEntryFormPage',
        ),
        migrations.AlterField(
            model_name='churchpage',
            name='locality_web',
            field=models.TextField(blank=True, help_text="Please type: 'http://' in the front of the URL", validators=[django.core.validators.URLValidator()]),
        ),
        migrations.AddField(
            model_name='churchentryformpagebullet',
            name='page',
            field=modelcluster.fields.ParentalKey(on_delete=django.db.models.deletion.CASCADE, related_name='bullet_points', to='lampstands.ChurchEntryFormPage'),
        ),
    ]