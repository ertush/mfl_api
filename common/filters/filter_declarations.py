import django_filters

from ..models import (
    ContactType,
    Contact,
    County,
    Constituency,
    Ward,
    UserCounty,
    PhysicalAddress,
    UserContact,
    Town,
    UserConstituency,
    SubCounty,
    DocumentUpload,
    ErrorQueue,
    UserSubCounty,
    Notification
)

from common.fields import SequenceField
from .filter_shared import (
    CommonFieldsFilterset,
    ListCharFilter,
    ListIntegerFilter
)


class NotificationFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = Notification


class UserSubCountyFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = UserSubCounty


class ErrorQueueFilter(django_filters.FilterSet):
    """
    ErrorQueue model does not descend from abtractbase thus the FilterSet.
    """

    class Meta(CommonFieldsFilterset.Meta):
        model = ErrorQueue


class SubCountyFilter(CommonFieldsFilterset):
    code = ListIntegerFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = SubCounty


class UserConstituencyFilter(CommonFieldsFilterset):
    county = django_filters.CharFilter(
        lookup_expr='exact', name='constituency__county')
    constituency = ListCharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = UserConstituency


class ContactTypeFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = ContactType


class ContactFilter(CommonFieldsFilterset):
    contact = django_filters.CharFilter(lookup_expr='icontains')
    contact_type = django_filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Contact


class PhysicalAddressFilter(CommonFieldsFilterset):
    town = django_filters.CharFilter(lookup_expr='exact')
    postal_code = django_filters.CharFilter(lookup_expr='icontains')
    address = django_filters.CharFilter(lookup_expr='icontains')
    nearest_landmark = django_filters.CharFilter(lookup_expr='icontains')
    plot_number = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = PhysicalAddress


class CountyFilter(CommonFieldsFilterset):
    name = ListCharFilter(lookup_expr='icontains')
    code = ListIntegerFilter(lookup_expr='exact')
    county_id = ListCharFilter(name='id', lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = County


class ConstituencyFilter(CommonFieldsFilterset):
    name = ListCharFilter(lookup_expr='icontains')
    code = ListIntegerFilter(lookup_expr='exact')
    county = ListCharFilter(lookup_expr='exact')
    constituency_id = ListCharFilter(name='id', lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Constituency


class WardFilter(CommonFieldsFilterset):
    ward_id = ListCharFilter(name='id', lookup_expr='exact')
    name = ListCharFilter(lookup_expr='icontains')
    code = ListIntegerFilter(lookup_expr='exact')
    constituency = ListCharFilter(lookup_expr='exact')
    sub_county = ListCharFilter(lookup_expr='exact')
    county = ListCharFilter(
        lookup_expr='exact', name='constituency__county')

    class Meta(CommonFieldsFilterset.Meta):
        model = Ward


class UserCountyFilter(CommonFieldsFilterset):
    user = django_filters.AllValuesFilter(lookup_expr='exact')
    county = django_filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = UserCounty


class UserContactFilter(CommonFieldsFilterset):
    user = django_filters.AllValuesFilter(lookup_expr='exact')
    contact = django_filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = UserContact


class TownFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = Town


class DocumentUploadFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = DocumentUpload
        exclude = ('fyl', )
