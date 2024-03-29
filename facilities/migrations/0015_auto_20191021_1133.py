# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-10-21 11:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0014_facilityupdates_is_national_approval'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facility',
            name='approved_national_level',
            field=models.BooleanField(help_text=b'Has the facility been approved at the national level'),
        ),
    ]
