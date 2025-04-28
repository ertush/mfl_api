import django_filters

from .models import (
    GeoCodeSource,
    GeoCodeMethod,
    FacilityCoordinates,
    WorldBorder,
    CountyBoundary,
    ConstituencyBoundary,
    WardBoundary
)

from common.filters.filter_shared import (
    CommonFieldsFilterset,
    ListCharFilter
)


class GeoCodeSourceFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    abbreviation = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = GeoCodeSource


class GeoCodeMethodFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = GeoCodeMethod


class FacilityCoordinatesFilter(CommonFieldsFilterset):

    ward = ListCharFilter(lookup_expr='exact', field_name='facility__ward')
    constituency = ListCharFilter(
        lookup_expr='exact', field_name='facility__ward__constituency'
    )
    county = ListCharFilter(
        lookup_expr='exact', field_name='facility__ward__constituency__county'
    )

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityCoordinates
        exclude = ('coordinates', )


class WorldBorderFilter(CommonFieldsFilterset):
    name = ListCharFilter(lookup_expr='icontains')
    code = ListCharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = WorldBorder
        exclude = ('mpoly', )


class CountyBoundaryFilter(CommonFieldsFilterset):
    id = ListCharFilter(lookup_expr='icontains')
    name = ListCharFilter(lookup_expr='icontains')
    code = ListCharFilter(lookup_expr='exact')
    area = ListCharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = CountyBoundary
        exclude = ('mpoly', )


class ConstituencyBoundaryFilter(CommonFieldsFilterset):
    id = ListCharFilter(lookup_expr='icontains')
    name = ListCharFilter(lookup_expr='icontains')
    code = ListCharFilter(lookup_expr='exact')
    area = ListCharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = ConstituencyBoundary
        exclude = ('mpoly', )


class WardBoundaryFilter(CommonFieldsFilterset):
    id = ListCharFilter(lookup_expr='icontains')
    name = ListCharFilter(lookup_expr='icontains')
    code = ListCharFilter(lookup_expr='exact')
    area = ListCharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = WardBoundary
        exclude = ('mpoly', )

