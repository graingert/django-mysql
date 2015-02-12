# -*- coding:utf-8 -*-
import json
import re

from django.core import exceptions, serializers
from django.db import models
from django.db.models import Q
from django.db.migrations.writer import MigrationWriter
from django.test import TestCase

from django_mysql.fields import SetCharField

from django_mysql_tests.models import Settee


class TestSaveLoad(TestCase):

    def test_easy(self):
        s = Settee.objects.create(features={"big", "comfy"})
        self.assertSetEqual(s.features, {"comfy", "big"})
        s = Settee.objects.get(id=s.id)
        self.assertSetEqual(s.features, {"comfy", "big"})

    def test_cant_create_sets_with_commas(self):
        with self.assertRaises(ValueError):
            Settee.objects.create(features={"co,ma", "contained"})

    def test_contains_lookup(self):
        sofa = Settee.objects.create(features={"mouldy", "rotten"})

        mouldy = Settee.objects.filter(features__contains="mouldy")
        self.assertEqual(mouldy.count(), 1)
        self.assertEqual(mouldy[0], sofa)

        rotten = Settee.objects.filter(features__contains="rotten")
        self.assertEqual(rotten.count(), 1)
        self.assertEqual(rotten[0], sofa)

        clean = Settee.objects.filter(features__contains="clean")
        self.assertEqual(clean.count(), 0)

        clean = Settee.objects.filter(features__contains={"mouldy", "rotten"})
        self.assertEqual(clean.count(), 0)

        either = Settee.objects.filter(
            Q(features__contains={"mouldy"}) | Q(features__contains={"clean"})
        )
        self.assertEqual(either.count(), 1)

        not_clean = Settee.objects.exclude(features__contains={"clean"})
        self.assertEqual(not_clean.count(), 1)

        not_mouldy = Settee.objects.exclude(features__contains={"mouldy"})
        self.assertEqual(not_mouldy.count(), 0)

    def test_len_lookup_empty(self):
        sofa = Settee.objects.create(features=set())

        empty = Settee.objects.filter(features__len=0)
        self.assertEqual(empty.count(), 1)
        self.assertEqual(empty[0], sofa)

        one = Settee.objects.filter(features__len=1)
        self.assertEqual(one.count(), 0)

        one_or_more = Settee.objects.filter(features__len__gte=0)
        self.assertEqual(one_or_more.count(), 1)

    def test_len_lookup(self):
        sofa = Settee.objects.create(features={"leather", "expensive"})

        empty = Settee.objects.filter(features__len=0)
        self.assertEqual(empty.count(), 0)

        one_or_more = Settee.objects.filter(features__len__gte=1)
        self.assertEqual(one_or_more.count(), 1)
        self.assertEqual(one_or_more[0], sofa)

        two = Settee.objects.filter(features__len=2)
        self.assertEqual(two.count(), 1)
        self.assertEqual(two[0], sofa)

        three = Settee.objects.filter(features__len=3)
        self.assertEqual(three.count(), 0)


class TestValidation(TestCase):

    def test_max_length(self):
        field = SetCharField(
            models.CharField(max_length=32),
            size=3,
            max_length=32
        )

        field.clean({'a', 'b', 'c'}, None)

        with self.assertRaises(exceptions.ValidationError) as cm:
            field.clean({'a', 'b', 'c', 'd'}, None)
        self.assertEqual(
            cm.exception.messages[0],
            'Set contains 4 items, it should contain no more than 3.'
        )


class TestCheck(TestCase):

    def test_field_checks(self):
        field = SetCharField(models.CharField(), max_length=32)
        field.set_attributes_from_name('field')
        errors = field.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'django_mysql.E001')

    def test_invalid_base_fields(self):
        field = SetCharField(
            models.ForeignKey('django_mysql_tests.Author'),
            max_length=32
        )
        field.set_attributes_from_name('field')
        errors = field.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'django_mysql.E002')

    def test_max_length_including_base(self):
        field = SetCharField(
            models.CharField(max_length=32),
            size=2, max_length=32)
        field.set_attributes_from_name('field')
        errors = field.check()
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0].id, 'django_mysql.E003')


class TestMigrations(TestCase):

    def test_deconstruct(self):
        field = SetCharField(models.IntegerField(), max_length=32)
        name, path, args, kwargs = field.deconstruct()
        new = SetCharField(*args, **kwargs)
        self.assertEqual(type(new.base_field), type(field.base_field))

    def test_deconstruct_with_size(self):
        field = SetCharField(models.IntegerField(), size=3, max_length=32)
        name, path, args, kwargs = field.deconstruct()
        new = SetCharField(*args, **kwargs)
        self.assertEqual(new.size, field.size)

    def test_deconstruct_args(self):
        field = SetCharField(models.CharField(max_length=5), max_length=32)
        name, path, args, kwargs = field.deconstruct()
        new = SetCharField(*args, **kwargs)
        self.assertEqual(
            new.base_field.max_length,
            field.base_field.max_length
        )

    def test_makemigrations(self):
        field = SetCharField(models.CharField(max_length=5), max_length=32)
        statement, imports = MigrationWriter.serialize(field)

        # The order of the output max_length/size statements varies by
        # python version, hence a little regexp to match them
        self.assertRegexpMatches(
            statement,
            re.compile(
                r"""^django_mysql\.fields\.SetCharField\(
                    models\.CharField\(max_length=5\),\ # space here
                    (
                        max_length=32,\ size=None|
                        size=None,\ max_length=32
                    )
                    \)$
                """,
                re.VERBOSE
            )
        )

    def test_makemigrations_with_size(self):
        field = SetCharField(
            models.CharField(max_length=5),
            max_length=32,
            size=5
        )
        statement, imports = MigrationWriter.serialize(field)

        # The order of the output max_length/size statements varies by
        # python version, hence a little regexp to match them
        self.assertRegexpMatches(
            statement,
            re.compile(
                r"""^django_mysql\.fields\.SetCharField\(
                    models\.CharField\(max_length=5\),\ # space here
                    (
                        max_length=32,\ size=5|
                        size=5,\ max_length=32
                    )
                    \)$
                """,
                re.VERBOSE
            )
        )


class TestSerialization(TestCase):

    def test_dumping(self):
        instance = Settee(features={"big", "comfy"})
        data = json.loads(serializers.serialize('json', [instance]))[0]
        features = data['fields']['features']
        self.assertEqual(sorted(features.split(',')), ["big", "comfy"])

    def test_loading(self):
        test_data = '''
            [{"fields": {"features": "big,leather,comfy"},
             "model": "django_mysql_tests.settee", "pk": null}]
        '''
        objs = list(serializers.deserialize('json', test_data))
        instance = objs[0].object
        self.assertEqual(instance.features, set(["big", "leather", "comfy"]))
