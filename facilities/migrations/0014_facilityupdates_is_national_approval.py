# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2019-09-11 16:37
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0013_facilityapproval_is_national_approval'),
    ]

    operations = [
        migrations.AddField(
            model_name='facilityupdates',
            name='is_national_approval',
            field=models.BooleanField(default=False, help_text=b'Approval of the facility at the national level'),
        ),
    ]
