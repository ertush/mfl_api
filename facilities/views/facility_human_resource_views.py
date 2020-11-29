from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework import status
from rest_framework.views import Response, APIView

from common.views import AuditableDetailViewMixin
from common.utilities import CustomRetrieveUpdateDestroyView

from ..models import (
    SpecialityCategory,
    Speciality,
    FacilitySpecialist
)

from ..serializers import (
    SpecialityCategorySerializer,
    SpecialitySerializer,
    FacilitySpecialistSerializer,
)
from ..filters import (
    SpecialityCategoryFilter,
    SpecialityFilter,
    FacilitySpecialistFilter,
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
    filter_class = FacilitySpecialistFilter
    ordering_fields = ('facility', 'speciality')


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
    # selected_option -- A speciality selected_option's pk
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