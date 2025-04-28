from rest_framework import generics
from rest_framework.views import Response

from common.views import AuditableDetailViewMixin
from common.models import UserCounty, UserSubCounty

from .models import AdminOffice, AdminOfficeContact
from .serializers import AdminOfficeSerializer, AdminOfficeContactSerializer
from .filters import AdminOfficeContactFilter, AdminOfficeFilter


class AdminOfficeListView(
        AuditableDetailViewMixin, generics.ListCreateAPIView):

    """
    Lists and creates admin offices
    Created ---  Date the admin office was Created
    Updated -- Date the admin office was Updated
    Created_by -- User who created the admin office
    Updated_by -- User who updated the admin office
    active  -- Boolean is the record active
    deleted -- Boolean is the record deleted
    name  -- Name of the admin office
    county --  The county of the admin office
    """
    def get_queryset(self, *args, **kwargs):
        report_type = self.request.query_params.get('report_type')
        is_national = self.request.query_params.get('is_national')

        if not report_type:
            user = self.request.user
            if user.county:
                return AdminOffice.objects.filter(
                    county_id__in=[
                        uc.county.id for uc in
                        UserCounty.objects.filter(user=user)
                    ])
            if user.sub_county:
                return AdminOffice.objects.filter(
                    county_id__in=[
                        us.sub_county.id for us in
                        UserSubCounty.objects.ilter(user=user)
                    ])
        if is_national == 'true':
            return AdminOffice.objects.filter(is_national=True)

        return AdminOffice.objects.all()

    queryset = AdminOffice.objects.all()
    serializer_class = AdminOfficeSerializer
    filterset_class = AdminOfficeFilter
    ordering_fields = (
        'county', 'name', 'sub_county', 'is_national')


class AdminOfficeDetailView(
        AuditableDetailViewMixin, generics.RetrieveUpdateDestroyAPIView):

    """
    Retrieves a particular Admin Office
    """
    queryset = AdminOffice.objects.all()
    serializer_class = AdminOfficeSerializer

    def delete(self, request, *args, **kwargs):
        obj = AdminOffice.objects.get(id=kwargs.get('pk'))
        AdminOfficeContact.objects.filter(admin_office=obj).delete()
        obj.delete()
        return Response(status=204)


class AdminOfficeContactListView(
        AuditableDetailViewMixin, generics.ListCreateAPIView):

    """
    Lists and creates admin offices cotacts
    Created ---  Date the admin office was Created
    Updated -- Date the admin office was Updated
    Created_by -- User who created the admin office
    Updated_by -- User who updated the admin office
    active  -- Boolean is the record active
    deleted -- Boolean is the record deleted
    contact_type -- The type of contact <pk>
    admin_office -- The admin_office <Pk>
    """
    queryset = AdminOfficeContact.objects.all()
    serializer_class = AdminOfficeContactSerializer
    filterset_class = AdminOfficeContactFilter
    ordering_fields = ('contact_type', 'contact',)


class AdminOfficeContactDetailView(
        AuditableDetailViewMixin, generics.RetrieveUpdateDestroyAPIView):

    """
    Retrieves a particular Admin Office Contact
    """
    queryset = AdminOfficeContact.objects.all()
    serializer_class = AdminOfficeContactSerializer
