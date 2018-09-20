import django_filters

from distutils.util import strtobool

from django.contrib.auth.models import Permission, Group

from common.filters import CommonFieldsFilterset
from common.constants import BOOLEAN_CHOICES, TRUTH_NESS

from .models import MflUser, ProxyGroup, CustomGroup


class MFLUserFilter(CommonFieldsFilterset):
    is_active = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = MflUser
        fields = ('is_active', )


class PermissionFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(object):
        model = Permission
        fields = '__all__'


class GroupFilter(django_filters.FilterSet):

    def get_by_name(self, qs, name, value):
        return Group.objects.filter(name__icontains=value)

    def get_county_level(self, qs, name, value):
        if value in TRUTH_NESS:
            cgs = [cg.group.id for cg in CustomGroup.objects.filter(
                county_level=True)]
        else:
            cgs = [cg.group.id for cg in CustomGroup.objects.filter(
                county_level=False)]
        return Group.objects.filter(id__in=cgs)

    def get_national_level(self, qs, name, value):
        if value in TRUTH_NESS:
            cgs = [cg.group.id for cg in CustomGroup.objects.filter(
                national=True)]
        else:
            cgs = [cg.group.id for cg in CustomGroup.objects.filter(
                national=False)]
        return Group.objects.filter(id__in=cgs)

    def get_sub_county_level(self, qs, name, value):
        if value in TRUTH_NESS:
            cgs = [cg.group.id for cg in CustomGroup.objects.filter(
                sub_county_level=True)]
        else:
            cgs = [cg.group.id for cg in CustomGroup.objects.filter(
                sub_county_level=False)]
        return Group.objects.filter(id__in=cgs)

    def get_regulator(self, qs, name, value):
        if value in TRUTH_NESS:
            cgs = [cg.group.id for cg in CustomGroup.objects.filter(
                regulator=True)]
        else:
            cgs = [cg.group.id for cg in CustomGroup.objects.filter(
                regulator=False)]
        return Group.objects.filter(id__in=cgs)

    name = django_filters.CharFilter(method='get_by_name')
    is_county_level = django_filters.CharFilter(method='get_county_level')
    is_national_level = django_filters.CharFilter(method='get_national_level')
    is_sub_county_level = django_filters.CharFilter(
        method='get_sub_county_level')
    is_regulator = django_filters.CharFilter(method='get_regulator')

    class Meta(object):
        model = ProxyGroup
        fields = '__all__'
