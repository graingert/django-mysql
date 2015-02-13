# -*- coding:utf-8 -*-
from __future__ import absolute_import

from django.core import checks
from django.db.models import (CharField, IntegerField, SubfieldBase,
                              Transform)
from django.db.models.lookups import Contains
from django.utils import six

from ..forms import SimpleSetField
from ..validators import SetMaxLengthValidator

__all__ = ['SetCharField']


class SetCharField(six.with_metaclass(SubfieldBase, CharField)):
    """
    A subclass of CharField for using MySQL's handy FIND_IN_SET function with.
    """
    def __init__(self, base_field, size=None, **kwargs):
        self.base_field = base_field
        self.size = size

        super(SetCharField, self).__init__(**kwargs)

        if self.size:
            self.validators.append(SetMaxLengthValidator(int(self.size)))

    def check(self, **kwargs):
        errors = super(SetCharField, self).check(**kwargs)
        if not isinstance(self.base_field, (CharField, IntegerField)):
            errors.append(
                checks.Error(
                    'Base field for set must be a CharField or IntegerField.',
                    hint=None,
                    obj=self,
                    id='django_mysql.E002'
                )
            )
        else:
            # Remove the field name checks as they are not needed here.
            base_errors = self.base_field.check()
            if base_errors:
                messages = '\n    '.join(
                    '%s (%s)' % (error.msg, error.id)
                    for error in base_errors
                )
                errors.append(
                    checks.Error(
                        'Base field for set has errors:\n    %s' % messages,
                        hint=None,
                        obj=self,
                        id='django_mysql.E001'
                    )
                )

            if isinstance(self.base_field, CharField) and self.size:
                max_size = (
                    (self.size * (self.base_field.max_length)) +
                    self.size - 1
                )
                if max_size > self.max_length:
                    errors.append(
                        checks.Error(
                            'Field can overrun - set contains CharFields of '
                            'max length %s, leading to a comma-combined max '
                            'length of %s, which is greater than the space '
                            'reserved for the set - %s' %
                            (self.base_field.max_length, max_size,
                                self.max_length),
                            hint=None,
                            obj=self,
                            id='django_mysql.E003'
                        )
                    )
        return errors

    @property
    def description(self):
        return 'Set of %s' % self.base_field.description

    def set_attributes_from_name(self, name):
        super(SetCharField, self).set_attributes_from_name(name)
        self.base_field.set_attributes_from_name(name)

    def deconstruct(self):
        name, path, args, kwargs = super(SetCharField, self).deconstruct()
        path = 'django_mysql.fields.SetCharField'
        args.insert(0, self.base_field)
        kwargs['size'] = self.size
        return name, path, args, kwargs

    def to_python(self, value):
        if isinstance(value, six.string_types):
            value = {self.base_field.to_python(v) for v in value.split(',')}
        return value

    def get_prep_value(self, value):
        if isinstance(value, set):
            value = {
                six.text_type(self.base_field.get_prep_value(v))
                for v in value
            }
            for v in value:
                if ',' in v:
                    raise ValueError("Set members in SetCharField %s cannot "
                                     "contain commas" % self.name)
            return ','.join(value)
        return value

    def get_db_prep_lookup(self, lookup_type, value, connection,
                           prepared=False):
        if lookup_type == 'contains':
            # Avoid the default behaviour of adding wildcards on either side of
            # what we're searching for, because FIND_IN_SET is doing that
            # implicitly
            if isinstance(value, set):
                # Can't do multiple contains without massive ORM hackery
                # (ANDing all the FIND_IN_SET calls), so just reject them
                raise ValueError("Can't do contains with a set and "
                                 "SetCharField, you should pass them as "
                                 "separate filters.")
            return [six.text_type(self.base_field.get_prep_value(value))]
        return super(SetCharField, self).get_db_prep_lookup(
            lookup_type, value, connection, prepared)

    def value_to_string(self, obj):
        vals = self._get_val_from_obj(obj)
        return self.get_prep_value(vals)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': SimpleSetField,
            'base_field': self.base_field.formfield(),
            'max_length': self.size,
        }
        defaults.update(kwargs)
        return super(SetCharField, self).formfield(**defaults)


@SetCharField.register_lookup
class SetContains(Contains):
    lookup_name = 'contains'

    def as_sql(self, qn, connection):
        lhs, lhs_params = self.process_lhs(qn, connection)
        rhs, rhs_params = self.process_rhs(qn, connection)
        params = lhs_params + rhs_params
        # Put rhs on the left since that's the order FIND_IN_SET uses
        return 'FIND_IN_SET(%s, %s)' % (rhs, lhs), params


@SetCharField.register_lookup
class SetLength(Transform):
    lookup_name = 'len'
    output_field = IntegerField()

    expr = (
        # No str.count equivalent in MySQL :(
        "("
        "CHAR_LENGTH(%s) -"
        "CHAR_LENGTH(REPLACE(%s, ',', '')) +"
        "IF(CHAR_LENGTH(%s), 1, 0)"
        ")"
    )

    def as_sql(self, compiler, connection):
        lhs, params = compiler.compile(self.lhs)
        return self.expr % (lhs, lhs, lhs), params
