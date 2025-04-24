from django.urls import include, path, re_path
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from common.views import APIRoot, root_redirect_view

from dj_rest_auth.views import (
    LoginView, LogoutView, UserDetailsView, PasswordChangeView,
    PasswordResetView, PasswordResetConfirmView
)

from rest_framework.authtoken.views import ObtainAuthToken
from django.contrib import admin

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
   openapi.Info(
      title="Kenya Master Health Facility Registry (KMHFR) API",
      default_version='v3',
      description="Kenya Master Health Facility Registry (KMHFR) API version 3",
      terms_of_service="https://api.kmhfltest.health.go.ke/terms/",
      contact=openapi.Contact(email="support@healthit.uonbi.ac.ke"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

rest_auth_patterns = (
    # re-written from rest_auth.urls because of cache validation
    # URLs that do not require a session or valid token
    path('password/reset/',
        cache_page(0)(PasswordResetView.as_view()),
        name='rest_password_reset'),
    path('password/reset/confirm/',
        cache_page(0)(PasswordResetConfirmView.as_view()),
        name='rest_password_reset_confirm'),
    path('login/',
        cache_page(0)(LoginView.as_view()), name='rest_login'),
    # URLs that require a user to be logged in with a valid session / token.
    path('logout/',
        cache_page(0)(LogoutView.as_view()), name='rest_logout'),
    path('user/',
        cache_page(0)(UserDetailsView.as_view()), name='rest_user_details'),
    path('password/change/',
        cache_page(0)(PasswordChangeView.as_view()), name='rest_password_change'),
)

app_name = 'api'

apipatterns = (
    path('', login_required(
        cache_page(60*60)(APIRoot.as_view())), name='root_listing'),
    # url(r'^explore/', include('rest_framework_swagger.urls',
    #     namespace='swagger')),
    path('common/', include('common.urls', namespace='common')),
    path('users/', include('users.urls', namespace='users')),
    path('facilities/', include('facilities.urls', namespace='facilities')),
    path('chul/', include('chul.urls', namespace='chul')),
    path('gis/', include('mfl_gis.urls', namespace='mfl_gis')),
    path('reporting/', include('reporting.urls', namespace='reporting')),
    path('admin_offices/', include('admin_offices.urls', namespace='admin_offices')),
    path('rest-auth/', include((rest_auth_patterns, None))),
    path('rest-auth/registration/', include('dj_rest_auth.registration.urls')),
    path('explore<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('explore/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('docs/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
)

urlpatterns = (
    path('', root_redirect_view, name='root_redirect'),
    path('admin/', admin.site.urls),
    path('api/', include((apipatterns, 'api'), namespace='api')),
    path('accounts/',
        include('rest_framework.urls', namespace='rest_framework')),
    re_path(r'^api/token/', ObtainAuthToken.as_view()),
    path('o/', include('oauth2_provider.urls')),
)
