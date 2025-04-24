from django.urls import path, re_path

from . import views

app_name = 'chul'

urlpatterns = (

    path('updates/', views.ChuUpdateBufferListView.as_view(),
        name='chu_updatebufers_list'),

    path('updates/<str:pk>/',
        views.ChuUpdateBufferDetailView.as_view(),
        name="chu_updatebuffer_detail"),

    path('services/', views.CHUServiceListView.as_view(),
        name='chu_services_list'),
    path('services/<str:pk>/',
        views.CHUServiceDetailView.as_view(), name="chu_service_detail"),

    path('statuses/', views.StatusListView.as_view(), name='statuses_list'),
    path('statuses/<str:pk>/',
        views.StatusDetailView.as_view(), name="status_detail"),

    path('unit_contacts/',
        views.CommunityHealthUnitContactListView.as_view(),
        name='community_health_unit_contacts_list'),
    path('unit_contacts/<str:pk>/',
        views.CommunityHealthUnitContactDetailView.as_view(),
        name="community_health_unit_contact_detail"),

    path('workers/', views.CommunityHealthWorkerListView.as_view(),
        name='community_health_workers_list'),
    path('workers/<str:pk>/',
        views.CommunityHealthWorkerDetailView.as_view(),
        name="community_health_worker_detail"),

    path('workers_contacts/',
        views.CommunityHealthWorkerContactListView.as_view(),
        name='community_health_worker_contacts_list'),
    path('workers_contacts/<str:pk>/',
        views.CommunityHealthWorkerContactDetailView.as_view(),
        name="community_health_worker_contact_detail"),


    path('units/',
        views.CommunityHealthUnitListView.as_view(),
        name='community_health_units_list'),
    path('units/<str:pk>/',
        views.CommunityHealthUnitDetailView.as_view(),
        name='community_health_unit_detail'),

    path('chu_ratings/',
        views.CHURatingListView.as_view(), name='chu_ratings'),
    re_path(r'^chu_ratings/(?P<pk>[a-z0-9\-]{32,32})/$',
        views.CHURatingDetailView.as_view(), name='chu_rating_detail'),

    path('units_detail_report/<str:pk>/',
        views.CHUDetailReport.as_view(), name='chu_detail_report'),

)
