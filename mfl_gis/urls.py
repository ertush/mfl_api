from django.conf import settings
from django.urls import path, re_path
from django.views.decorators.cache import cache_page
from django.views.decorators.gzip import gzip_page

from .views import (
    GeoCodeSourceListView,
    GeoCodeSourceDetailView,
    GeoCodeMethodListView,
    GeoCodeMethodDetailView,
    FacilityCoordinatesListView,
    FacilityCoordinatesDetailView,
    WorldBorderListView,
    CountyBoundaryListView,
    ConstituencyBoundaryListView,
    WardBoundaryListView,
    WorldBorderDetailView,
    CountyBoundaryDetailView,
    ConstituencyBoundaryDetailView,
    WardBoundaryDetailView,
    FacilityCoordinatesCreationAndListing,
    FacilityCoordinatesCreationAndDetail,
    ConstituencyBoundView,
    CountyBoundView,
    IkoWapi,
    DrillFacilityCoords,
    DrillCountryBorders,
    DrillCountyBorders,
    DrillConstituencyBorders,
    DrillWardBorders,
)


cache_seconds = settings.GIS_BORDERS_CACHE_SECONDS
coordinates_cache_seconds = (60 * 60 * 24)

app_name = 'gis'

urlpatterns = (
    path(
        'drilldown/facility/',
        cache_page(60*60)(DrillFacilityCoords.as_view()),
        name='drilldown_facility'
    ),
    path(
        'drilldown/country/',
        cache_page(coordinates_cache_seconds)(DrillCountryBorders.as_view()),
        name='drilldown_country'
    ),
    re_path(
        r'^drilldown/county/(?P<code>\d{1,5})/$',
        cache_page(coordinates_cache_seconds)(DrillCountyBorders.as_view()),
        name='drilldown_county'
    ),
    re_path(
        r'^drilldown/constituency/(?P<code>\d{1,5})/$',
        cache_page(coordinates_cache_seconds)(
            DrillConstituencyBorders.as_view()
        ),
        name='drilldown_constituency'
    ),
    re_path(
        r'^drilldown/ward/(?P<code>\d{1,5})/$',
        cache_page(coordinates_cache_seconds)(DrillWardBorders.as_view()),
        name='drilldown_ward'
    ),

    path('ikowapi/', IkoWapi.as_view(), name='ikowapi'),

    path('geo_code_sources/',
        GeoCodeSourceListView.as_view(),
        name='geo_code_sources_list'),
    path('geo_code_sources/<str:pk>/',
        GeoCodeSourceDetailView.as_view(),
        name='geo_code_source_detail'),

    path('geo_code_methods/',
        GeoCodeMethodListView.as_view(),
        name='geo_code_methods_list'),
    path('geo_code_methods/<str:pk>/',
        GeoCodeMethodDetailView.as_view(),
        name='geo_code_method_detail'),

    path('facility_coordinates/<str:pk>/',
        FacilityCoordinatesCreationAndDetail.as_view(),
        name='facility_coordinates_simple_detail'),

    path('facility_coordinates/',
        FacilityCoordinatesCreationAndListing.as_view(),
        name='facility_coordinates_simple_list'),
    path('coordinates/',
        gzip_page(
            cache_page(coordinates_cache_seconds)
            (FacilityCoordinatesListView.as_view())),
        name='facility_coordinates_list'),
    path('coordinates/<str:pk>/',
        gzip_page(
            cache_page(coordinates_cache_seconds)
            (FacilityCoordinatesDetailView.as_view())),
        name='facility_coordinates_detail'),

    path('country_borders/',
        gzip_page(
            cache_page(cache_seconds)
            (WorldBorderListView.as_view())),
        name='world_borders_list'),
    path('country_borders/<str:pk>/',
        gzip_page(
            cache_page(cache_seconds)
            (WorldBorderDetailView.as_view())),
        name='world_border_detail'),

    path('county_boundaries/',
        gzip_page(
            cache_page(cache_seconds)
            (CountyBoundaryListView.as_view())),
        name='county_boundaries_list'),
    path('county_boundaries/<str:pk>/',
        gzip_page(
            cache_page(cache_seconds)
            (CountyBoundaryDetailView.as_view())),
        name='county_boundary_detail'),
    path('county_bound/<str:pk>/',
        gzip_page(
            cache_page(cache_seconds)
            (CountyBoundView.as_view())),
        name='county_bound'),

    path('constituency_boundaries/',
        gzip_page(
            cache_page(cache_seconds)
            (ConstituencyBoundaryListView.as_view())),
        name='constituency_boundaries_list'),
    path('constituency_boundaries/<str:pk>/',
        gzip_page(
            cache_page(cache_seconds)
            (ConstituencyBoundaryDetailView.as_view())),
        name='constituency_boundary_detail'),

    path('constituency_bound/<str:pk>/',
        gzip_page(
            cache_page(cache_seconds)
            (ConstituencyBoundView.as_view())),
        name='constituency_bound'),

    path('ward_boundaries/',
        gzip_page(
            cache_page(cache_seconds)
            (WardBoundaryListView.as_view())),
        name='ward_boundaries_list'),
    path('ward_boundaries/<str:pk>/',
        gzip_page(
            cache_page(cache_seconds)
            (WardBoundaryDetailView.as_view())),
        name='ward_boundary_detail'),
)
