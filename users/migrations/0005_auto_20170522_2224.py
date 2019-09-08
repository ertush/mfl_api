# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20160701_0723'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mfloauthapplication',
            name='user',
            field=models.ForeignKey(related_name='users_mfloauthapplication', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]
