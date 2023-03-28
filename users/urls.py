from __future__ import unicode_literals
from django.conf.urls import url

from .views import (
    UserList,
    UserDetailView,
    MFLOauthApplicationListView,
    MFLOauthApplicationDetailView,
    PermissionsListView,
    GroupListView,
    GroupDetailView
)


urlpatterns = (

    url(r'^applications/$', MFLOauthApplicationListView.as_view(),
        name='mfl_oauth_applications_list'),
    url(r'^applications/(?P<pk>[^/]+)/$',
        MFLOauthApplicationDetailView.as_view(),
        name='mfl_oauth_application_detail'),

    url(r'^groups/$', GroupListView.as_view(), name='groups_list'),
    url(r'^groups/(?P<pk>[^/]+)/$', GroupDetailView.as_view(),
        name='group_detail'),

    url(r'^permissions/$', PermissionsListView.as_view(),
        name='permissions_list'),

    url(r'^$', UserList.as_view(), name='mfl_users_list'),
    url(r'^(?P<pk>[^/]+)/$', UserDetailView.as_view(),
        name='mfl_user_detail'),
    #Reset Password urls
    path('password_reset/',auth_views.PasswordResetView.as_view(),name='password_reset'),
    path('password_reset/done/',auth_views.PasswordResetDoneView.as_view(),name='password_reset_done'),
    path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(),name='password_reset_confirm'),
    path('reset/done/',auth_views.PasswordResetCompleteView.as_view(),name='password_reset_complete'),
)
