from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework import status
from rest_framework.views import Response, APIView

from common.views import AuditableDetailViewMixin
from common.utilities import CustomRetrieveUpdateDestroyView

from ..models import (
    SpecialityCategory,
    Speciality,
    FacilitySpecialist,
    InfrastructureCategory,
    Infrastructure,
    FacilityInfrastructure
)

from ..serializers import (
    SpecialityCategorySerializer,
    SpecialitySerializer,
    FacilitySpecialistSerializer,
    InfrastructureCategorySerializer,
    InfrastructureSerializer,
    FacilityInfrastructureSerializer,
)
from ..filters import (
    SpecialityCategoryFilter,
    SpecialityFilter,
    FacilitySpecialistFilter,
    InfrastructureCategoryFilter,
    InfrastructureFilter,
    FacilityInfrastructureFilter
)


class SpecialityCategoryListView(generics.ListCreateAPIView):
    """
    Lists and creates service categories.

    Created ---  Date the record was Created
    Updated -- Date the record was Updated
    Created_by -- User who created the record
    Updated_by -- User who updated the record
    active  -- Boolean is the record active
    deleted -- Boolean is the record deleted
    """
    queryset = SpecialityCategory.objects.all()
    serializer_class = SpecialityCategorySerializer
    filter_class = SpecialityCategoryFilter
    ordering_fields = ('name', 'description', 'abbreviation')


class SpecialityCategoryDetailView(
        AuditableDetailViewMixin, CustomRetrieveUpdateDestroyView):
    """
    Retrieves a particular speciality category.
    """
    queryset = SpecialityCategory.objects.all()
    serializer_class = SpecialityCategorySerializer


class SpecialityListView(generics.ListCreateAPIView):
    """
    Lists and creates specialities.

    category -- Speciality category pk
    Created --  Date the record was Created
    Updated -- Date the record was Updated
    Created_by -- User who created the record
    Updated_by -- User who updated the record
    active  -- Boolean is the record active
    deleted -- Boolean is the record deleted
    """
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer
    filter_class = SpecialityFilter
    ordering_fields = ('created', 'name')


class SpecialityDetailView(
        AuditableDetailViewMixin, CustomRetrieveUpdateDestroyView):
    """
    Retrieves a particular speciality detail
    """
    queryset = Speciality.objects.all()
    serializer_class = SpecialitySerializer


class FacilitySpecialistListView(generics.ListCreateAPIView):
    """
    Lists and creates links between facilities and specialists.

    facility -- A facility's pk
    Created --  Date the record was Created
    Updated -- Date the record was Updated
    Created_by -- User who created the record
    Updated_by -- User who updated the record
    active  -- Boolean is the record active
    deleted -- Boolean is the record deleted
    """
    queryset = FacilitySpecialist.objects.all()
    serializer_class = FacilitySpecialistSerializer
    filter_class = FacilitySpecialistFilter
    ordering_fields = ('facility', 'service')


class FacilitySpecialistDetailView(
        AuditableDetailViewMixin, CustomRetrieveUpdateDestroyView):
    """
    Retrieves a particular facility service detail
    """
    queryset = FacilitySpecialist.objects.all()
    serializer_class = FacilitySpecialistSerializer


# Infrustructure
class InfrastructureCategoryListView(generics.ListCreateAPIView):
    """
    Lists and creates service categories.

    Created ---  Date the record was Created
    Updated -- Date the record was Updated
    Created_by -- User who created the record
    Updated_by -- User who updated the record
    active  -- Boolean is the record active
    deleted -- Boolean is the record deleted
    """
    queryset = InfrastructureCategory.objects.all()
    serializer_class = InfrastructureCategorySerializer
    filter_class = InfrastructureCategoryFilter
    ordering_fields = ('name', 'description', 'abbreviation')


class InfrastructureCategoryDetailView(
        AuditableDetailViewMixin, CustomRetrieveUpdateDestroyView):
    """
    Retrieves a particular speciality category.
    """
    queryset = InfrastructureCategory.objects.all()
    serializer_class = InfrastructureCategorySerializer


class InfrastructureListView(generics.ListCreateAPIView):
    """
    Lists and creates specialities.

    category -- Infrastructure category pk
    Created --  Date the record was Created
    Updated -- Date the record was Updated
    Created_by -- User who created the record
    Updated_by -- User who updated the record
    active  -- Boolean is the record active
    deleted -- Boolean is the record deleted
    """
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer
    filter_class = InfrastructureFilter
    ordering_fields = ('created', 'name')


class InfrastructureDetailView(
        AuditableDetailViewMixin, CustomRetrieveUpdateDestroyView):
    """
    Retrieves a particular speciality detail
    """
    queryset = Infrastructure.objects.all()
    serializer_class = InfrastructureSerializer


class FacilityInfrastructureListView(generics.ListCreateAPIView):
    """
    Lists and creates links between facilities and specialists.

    facility -- A facility's pk
    Created --  Date the record was Created
    Updated -- Date the record was Updated
    Created_by -- User who created the record
    Updated_by -- User who updated the record
    active  -- Boolean is the record active
    deleted -- Boolean is the record deleted
    """
    queryset = FacilityInfrastructure.objects.all()
    serializer_class = FacilityInfrastructureSerializer
    filter_class = FacilityInfrastructureFilter
    ordering_fields = ('facility', 'service')


class FacilityInfrastructureDetailView(
        AuditableDetailViewMixin, CustomRetrieveUpdateDestroyView):
    """
    Retrieves a particular facility service detail
    """
    queryset = FacilityInfrastructure.objects.all()
    serializer_class = FacilityInfrastructureSerializer