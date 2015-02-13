# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

import django_mysql.fields


class Migration(migrations.Migration):

    dependencies = [
        ('django_mysql_tests', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='integersetdefaultmodel',
            name='field_2',
            field=django_mysql.fields.SetCharField(models.IntegerField(),
                                                   default=set(),
                                                   size=None,
                                                   max_length=32),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='integersetdefaultmodel',
            name='field_3',
            field=django_mysql.fields.SetCharField(models.IntegerField(),
                                                   default={1, 5},
                                                   size=None,
                                                   max_length=32),
            preserve_default=False,
        ),
    ]
