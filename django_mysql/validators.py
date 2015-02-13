# -*- coding:utf-8 -*-
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.utils.translation import ungettext_lazy


class SetMaxLengthValidator(MaxLengthValidator):
    message = ungettext_lazy(
        'Set contains %(show_value)d item, '
        'it should contain no more than %(limit_value)d.',

        'Set contains %(show_value)d items, '
        'it should contain no more than %(limit_value)d.',

        'limit_value'
    )


class SetMinLengthValidator(MinLengthValidator):
    message = ungettext_lazy(
        'Set contains %(show_value)d item, '
        'it should contain no fewer than %(limit_value)d.',

        'Set contains %(show_value)d items, '
        'it should contain no fewer than %(limit_value)d.',

        'limit_value'
    )
