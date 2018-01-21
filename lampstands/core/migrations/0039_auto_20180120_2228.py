# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2018-01-21 04:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lampstands', '0038_auto_20180120_2210'),
    ]

    operations = [
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_one',
            new_name='locality_contact_brother_1',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_one_phone',
            new_name='locality_contact_brother_1_phone',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_two',
            new_name='locality_contact_brother_2',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_two_phone',
            new_name='locality_contact_brother_2_phone',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_three',
            new_name='locality_contact_brother_3',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_three_phone',
            new_name='locality_contact_brother_3_phone',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_four',
            new_name='locality_contact_brother_4',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_four_phone',
            new_name='locality_contact_brother_4_phone',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_five',
            new_name='locality_contact_brother_5',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_five_phone',
            new_name='locality_contact_brother_5_phone',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_six',
            new_name='locality_contact_brother_6',
        ),
        migrations.RenameField(
            model_name='churchpage',
            old_name='locality_contact_brother_six_phone',
            new_name='locality_contact_brother_6_phone',
        ),
        migrations.AddField(
            model_name='churchpage',
            name='mailing_address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]