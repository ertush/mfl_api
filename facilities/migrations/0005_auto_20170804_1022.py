# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('facilities', '0004_auto_20170804_0948'),
    ]

    operations = [
        migrations.AlterField(
            model_name='facilityregulationstatus',
            name='regulating_body',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='facilities.RegulatingBody', null=True),
        ),
    ]
