# -*- coding: utf-8 -*-
# Generated by Django 1.11.27 on 2023-03-23 06:57
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0023_auto_20230321_0937'),
    ]

    operations = [
        migrations.AddField(
            model_name='facility',
            name='mydate',
            field=models.DateField(default=datetime.date.today),
        ),
    ]
