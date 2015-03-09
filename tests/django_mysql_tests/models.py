# -*- coding:utf-8 -*-
from django.db.models import CharField, IntegerField, Model as VanillaModel

from django_mysql.models import Model, SetCharField, SetTextField


class CharSetModel(Model):
    field = SetCharField(
        base_field=CharField(max_length=8),
        size=3,
        max_length=32,
    )


class IntSetModel(Model):
    field = SetCharField(base_field=IntegerField(), size=5, max_length=32)


class CharSetDefaultModel(Model):
    field = SetCharField(base_field=CharField(max_length=5),
                         size=5,
                         max_length=32,
                         default=lambda: {"a", "d"})


class BigCharSetModel(Model):
    field = SetTextField(
        base_field=CharField(max_length=8),
        max_length=32,
    )


class BigIntSetModel(Model):
    field = SetTextField(base_field=IntegerField())


class Author(Model):
    name = CharField(max_length=32)


class VanillaAuthor(VanillaModel):
    name = CharField(max_length=32)


class NameAuthor(Model):
    name = CharField(max_length=32, primary_key=True)
