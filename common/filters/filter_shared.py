import django_filters
from django_filters import rest_framework as filters
import uuid

from distutils.util import strtobool
from rest_framework.exceptions import ValidationError

from django import forms
from django.utils.encoding import force_str
from django.utils.dateparse import parse_datetime

from rest_framework import ISO_8601

from search.filters import ClassicSearchFilter, AutoCompleteSearchFilter

from ..constants import BOOLEAN_CHOICES


class NullFilter(django_filters.Filter):
    """
    Filter a field on whether it is null or not.
    """

    def filter(self, qs, value):
        if value is None:
            return qs

        value_str = str(value).strip().lower()
        if value_str not in ('true', 'false'):
            return qs  # Ignore invalid values

        return qs.filter(**{f"{self.field_name}__isnull": value_str == 'true'})


class IsoDateTimeField(forms.DateTimeField):
    """
    It support 'iso-8601' date format too which is out the scope of
    the ``datetime.strptime`` standard library

    # ISO 8601: ``http://www.w3.org/TR/NOTE-datetime``
    """

    def strptime(self, value, format):
        value = force_str(value)
        if format == ISO_8601:
            parsed = parse_datetime(value)
            if parsed is None:  # Continue with other formats if doesn't match
                raise ValueError
            return parsed
        return super(IsoDateTimeField, self).strptime(value, format)


class IsoDateTimeFilter(django_filters.DateTimeFilter):
    """ Extend ``DateTimeFilter`` to filter by ISO 8601 formated dates too"""
    field_class = IsoDateTimeField


class ListFilterMixin:
    """
    Mixin to enable filtering by comma-separated values.
    """
    _lookup_expr = 'in'
    _customize_fxn = staticmethod(lambda v: v)  # By default, no customization

    def sanitize(self, value_list):
        return [v for v in value_list if v]

    def customize(self, value):
        return self._customize_fxn(value)

    def filter(self, qs, value):
        if not value:
            return qs

        if isinstance(value, (list, tuple)):
            multiple_vals = self.sanitize(value)
        else:
            multiple_vals = self.sanitize(value.split(","))

        if not multiple_vals:
            return qs

        try:
            multiple_vals = [self.customize(v) for v in multiple_vals]
        except (ValueError, TypeError) as e:
            # Optional: raise a 400 API error instead of ignoring
            return qs  # or raise ValidationError('Invalid input.')

        lookup = {self.field_name: multiple_vals} if self._lookup_expr == 'in' else {
            f"{self.field_name}__{self._lookup_expr}": multiple_vals
        }
        return qs.filter(**lookup)


class ListCharFilter(ListFilterMixin, django_filters.CharFilter):
    """
    Enable filtering of comma separated strings.
    """
    pass


class ListUUIDFilter(django_filters.Filter):
    """
    Accept a single UUID or multiple comma-separated UUIDs.
    """

    def filter(self, qs, value):
        if not value:
            return qs

        if isinstance(value, list):
            uuid_list = value
        else:
            uuid_list = value.split(",")

        # Clean and validate
        clean_uuids = []
        for val in uuid_list:
            val = val.strip()
            if not val:
                continue
            try:
                clean_uuids.append(uuid.UUID(val))
            except (ValueError, AttributeError):
                raise ValidationError(f"Invalid UUID: {val}")

        if not clean_uuids:
            return qs

        return qs.filter(**{f"{self.field_name}__in": clean_uuids})


class ListIntegerFilter(ListCharFilter):
    """
    Enable filtering of comma separated integers.
    """

    _customize_fxn = int


class CommonFieldsFilterset(filters.FilterSet):
    """Every model that descends from AbstractBase should have this

    The usage pattern for this is presently simplistic; mix it in, then add to
    the `fields` in the filter's `Meta` `'updated', 'created',
    updated_before', 'created_before', 'updated_after', 'created_after'' and
    any other applicable / extra fields.

    When you inherit this, DO NOT add a `fields` declaration. Let the implicit
    filter fields ( every model field gets one ) stay in place.
    """
    updated_before = IsoDateTimeFilter(
        field_name='updated', lookup_expr='lte',
        input_formats=(ISO_8601, '%m/%d/%Y %H:%M:%S'))
    created_before = IsoDateTimeFilter(
        field_name='created', lookup_expr='lte',
        input_formats=(ISO_8601, '%m/%d/%Y %H:%M:%S'))

    updated_after = IsoDateTimeFilter(
        field_name='updated', lookup_expr='gte',
        input_formats=(ISO_8601, '%m/%d/%Y %H:%M:%S'))
    created_after = IsoDateTimeFilter(
        field_name='created', lookup_expr='gte',
        input_formats=(ISO_8601, '%m/%d/%Y %H:%M:%S'))

    updated_on = IsoDateTimeFilter(
        field_name='updated', lookup_expr='exact',
        input_formats=(ISO_8601, '%m/%d/%Y %H:%M:%S'))
    created_on = IsoDateTimeFilter(
        field_name='created', lookup_expr='exact',
        input_formats=(ISO_8601, '%m/%d/%Y %H:%M:%S'))

    is_deleted = django_filters.TypedChoiceFilter(
        field_name='deleted', choices=BOOLEAN_CHOICES, coerce=strtobool)

    is_active = django_filters.TypedChoiceFilter(
        field_name='active', choices=BOOLEAN_CHOICES, coerce=strtobool)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        model = getattr(getattr(self, 'Meta', None), 'model', None)
        if model and hasattr(model, '_meta'):
            fields = {f.name for f in model._meta.get_fields()}
            if 'name' in fields:
                self.filters['search'] = filters.CharFilter(field_name='name', lookup_expr='icontains')
                self.filters['q'] = filters.CharFilter(field_name='name', lookup_expr='icontains')
                self.filters['search_auto'] = filters.CharFilter(field_name='name', lookup_expr='icontains')
                self.filters['q_auto'] = filters.CharFilter(field_name='name', lookup_expr='icontains')

    class Meta:
        fields = '__all__'
