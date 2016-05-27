# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('category', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ctgstatus',
            name='exclusion',
        ),
        migrations.AddField(
            model_name='ctgstatus',
            name='exclusions',
            field=models.ManyToManyField(related_name='exclusions_rel_+', to='category.CtgStatus', blank=True),
        ),
    ]
