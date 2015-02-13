# -*- coding:utf-8 -*-
from django.db.models import CharField, IntegerField, Model as VanillaModel

from django_mysql.fields import SetCharField
from django_mysql.models import Model


class CharSetModel(Model):
    field = SetCharField(
        base_field=CharField(max_length=8),
        size=3,
        max_length=32,
    )


class IntSetModel(Model):
    field = SetCharField(base_field=IntegerField(), size=5, max_length=32)


class Author(Model):
    name = CharField(max_length=32)


class VanillaAuthor(VanillaModel):
    name = CharField(max_length=32)


class NameAuthor(Model):
    name = CharField(max_length=32, primary_key=True)
