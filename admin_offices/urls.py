from django.urls import path

from . import views

app_name = 'admin_offices'

urlpatterns = (

    path('contacts/',
        views.AdminOfficeContactListView.as_view(),
        name='admin_office_contacts_list'),

    path('contacts/<str:pk>/',
        views.AdminOfficeContactDetailView.as_view(),
        name="admin_office_contact_detail"),

    path('<str:pk>/',
        views.AdminOfficeDetailView.as_view(),
        name="admin_office_detail"),
    path('',
        views.AdminOfficeListView.as_view(),
        name='admin_offices_list'),

)
