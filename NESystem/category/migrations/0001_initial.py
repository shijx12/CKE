# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CtgStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('category', models.CharField(max_length=100, db_index=True)),
                ('status', models.IntegerField(default=0)),
                ('exclusion', models.ManyToManyField(related_name='exclusion_rel_+', to='category.CtgStatus')),
            ],
        ),
    ]
