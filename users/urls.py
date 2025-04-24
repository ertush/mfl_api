from __future__ import unicode_literals
from django.urls import path

from .views import (
    UserList,
    UserDetailView,
    MFLOauthApplicationListView,
    MFLOauthApplicationDetailView,
    PermissionsListView,
    GroupListView,
    GroupDetailView
)

app_name = 'users'

urlpatterns = (

    path('applications/', MFLOauthApplicationListView.as_view(),
        name='mfl_oauth_applications_list'),
    path('applications/<str:pk>/',
        MFLOauthApplicationDetailView.as_view(),
        name='mfl_oauth_application_detail'),

    path('groups/', GroupListView.as_view(), name='groups_list'),
    path('groups/<str:pk>/', GroupDetailView.as_view(),
        name='group_detail'),

    path('permissions/', PermissionsListView.as_view(),
        name='permissions_list'),

    path('', UserList.as_view(), name='mfl_users_list'),
    path('<str:pk>/', UserDetailView.as_view(),
        name='mfl_user_detail'),
)
