import django_filters
from django.db.models import Q
from distutils.util import strtobool


from .models import (
    CommunityHealthUnit,
    CommunityHealthWorker,
    CommunityHealthWorkerContact,
    Status,
    CommunityHealthUnitContact,
    CHUService,
    CHURating,
    ChuUpdateBuffer
)


from common.filters.filter_shared import (
    CommonFieldsFilterset,
    ListCharFilter)

from common.constants import BOOLEAN_CHOICES, TRUTH_NESS


class ChuUpdateBufferFilter(CommonFieldsFilterset):

    class Meta(CommonFieldsFilterset.Meta):
        model = ChuUpdateBuffer


class CHUServiceFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = CHUService


class StatusFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = Status


class CommunityHealthUnitContactFilter(CommonFieldsFilterset):
    health_unit = django_filters.AllValuesFilter(lookup_expr='exact')
    contact = django_filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = CommunityHealthUnitContact


class CommunityHealthUnitFilter(CommonFieldsFilterset):

    def chu_pending_approval(self, qs, name, value):
        if value in TRUTH_NESS:
            return qs.filter(
                Q(is_approved=False, is_rejected=False, has_edits=False) |
                Q(is_approved=True, is_rejected=False, has_edits=True) |
                Q(is_approved=False, is_rejected=True, has_edits=True)
            )
        else:
            return qs.filter(
                Q(is_approved=True, is_rejected=False, has_edits=False) |
                Q(is_approved=False, is_rejected=True, has_edits=False)
            )
    name = django_filters.CharFilter(lookup_expr='icontains')
    ward = ListCharFilter(name='facility__ward')
    code = ListCharFilter(name='code')
    constituency = ListCharFilter(
        name='facility__ward__constituency')
    county = ListCharFilter(
        name='facility__ward__constituency__county')
    sub_county = ListCharFilter(
        name='facility__ward__sub_county')

    is_approved = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )
    is_rejected = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )
    has_edits = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )
    pending_approval = django_filters.CharFilter(
        method='chu_pending_approval')

    class Meta(CommonFieldsFilterset.Meta):
        model = CommunityHealthUnit


class CommunityHealthWorkerFilter(CommonFieldsFilterset):
    first_name = django_filters.CharFilter(lookup_expr='icontains')
    last_name = django_filters.CharFilter(lookup_expr='icontains')
    username = django_filters.CharFilter(lookup_expr='icontains')
    ward = django_filters.CharFilter(name='health_unit__community__ward')
    constituency = django_filters.CharFilter(
        name='health_unit__community_ward__constituency')
    county = django_filters.CharFilter(
        name='health_unit__community__ward__constituency__county')

    class Meta(CommonFieldsFilterset.Meta):
        model = CommunityHealthWorker


class CommunityHealthWorkerContactFilter(CommonFieldsFilterset):
    health_worker = django_filters.AllValuesFilter(lookup_expr='exact')
    contact = django_filters.AllValuesFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = CommunityHealthWorkerContact


class CHURatingFilter(CommonFieldsFilterset):
    chu = django_filters.AllValuesFilter(lookup_expr='exact')
    rating = django_filters.NumberFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = CHURating
