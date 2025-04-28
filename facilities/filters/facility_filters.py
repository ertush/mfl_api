from distutils.util import strtobool
from random import choices

import django_filters
from django.db.models import Q

from django_filters import rest_framework as filters
from ..models import (
    Owner,
    Facility,
    JobTitle,
    FacilityUnit,
    FacilityStatus,
    FacilityAdmissionStatus,
    Officer,
    RegulatingBody,
    OwnerType,
    OfficerContact,
    FacilityContact,
    FacilityRegulationStatus,
    FacilityType,
    RegulationStatus,
    ServiceCategory,
    Option,
    Service,
    FacilityService,
    SpecialityCategory,
    Speciality,
    FacilitySpecialist,
    FacilityApproval,
    FacilityOperationState,
    FacilityUpgrade,
    RegulatingBodyContact,
    FacilityServiceRating,
    FacilityOfficer,
    RegulatoryBodyUser,
    FacilityUnitRegulation,
    FacilityUpdates,
    KephLevel,
    OptionGroup,
    FacilityLevelChangeReason,
    FacilityDepartment,
    RegulatorSync,
    FacilityExportExcelMaterialView,
    InfrastructureCategory,
    Infrastructure,
    FacilityInfrastructure
)
from common.constants import BOOLEAN_CHOICES, TRUTH_NESS
from common.filters.filter_shared import (
    CommonFieldsFilterset,
    ListIntegerFilter,
    ListCharFilter,
    NullFilter,
    ListUUIDFilter
)
from search.filters import ClassicSearchFilter


class FacilityExportExcelMaterialViewFilter(filters.FilterSet):

    def filter_number_beds(self, qs, name, value):
        return qs.filter(beds__gte=1)

    def filter_number_cots(self, qs, name, value):
        return qs.filter(cots__gte=1)

    search = ClassicSearchFilter(field_name='search')
    county = ListCharFilter(lookup_expr='exact')
    code = ListCharFilter(lookup_expr='exact')
    constituency = ListCharFilter(lookup_expr='exact')
    ward = ListCharFilter(lookup_expr='exact')
    owner = ListCharFilter(lookup_expr='exact')
    owner_type = ListCharFilter(lookup_expr='exact')
    number_of_beds = filters.CharFilter(method='filter_number_beds')
    number_of_cots = filters.CharFilter(method='filter_number_cots')
    open_whole_day = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_late_night = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_weekends = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_public_holidays = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    keph_level = ListCharFilter(lookup_expr='exact')
    facility_type = ListCharFilter(lookup_expr='exact')
    operation_status = ListCharFilter(lookup_expr='exact')
    service = ListUUIDFilter(lookup_expr='exact', name='services')
    service_category = ListUUIDFilter(lookup_expr='exact', name='categories')
    service_name = ClassicSearchFilter(field_name='service_names')
    approved_national_level = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityExportExcelMaterialView
        exclude = ('services', 'categories', 'service_names', 'infrastructure', 'infrastructure_names',
                   'infrastructure_categories', 'speciality', 'speciality_names', 'speciality_categories')


class RegulatorSyncFilter(CommonFieldsFilterset):
    mfl_code_null = NullFilter(field_name='mfl_code')
    county = ListCharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = RegulatorSync


class OptionGroupFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = OptionGroup


class FacilityLevelChangeReasonFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityLevelChangeReason


class KephLevelFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = KephLevel


class FacilityUpdatesFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityUpdates


class RegulatoryBodyUserFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = RegulatoryBodyUser


class FacilityOfficerFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityOfficer


class FacilityServiceRatingFilter(CommonFieldsFilterset):
    facility = filters.AllValuesFilter(
        field_name='facility_service__facility',
        lookup_expr='exact')
    service = filters.AllValuesFilter(
        field_name="facility_service__service", lookup_expr='exact')
    county = filters.AllValuesFilter(
        field_name="facility_service__facility__ward__constituency__county",
        lookup_expr='exact')
    constituency = filters.AllValuesFilter(
        field_name="facility_service__facility__ward__constituency",
        lookup_expr='exact')
    ward = filters.AllValuesFilter(
        field_name="facility_service__facility__ward", lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityServiceRating


class RegulatingBodyContactFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = RegulatingBodyContact


class FacilityUpgradeFilter(CommonFieldsFilterset):
    is_confirmed = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    is_cancelled = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityUpgrade


class FacilityOperationStateFilter(CommonFieldsFilterset):
    operation_status = filters.AllValuesFilter(lookup_expr='exact')
    facility = filters.AllValuesFilter(lookup_expr='exact')
    reason = filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityOperationState


class FacilityApprovalFilter(CommonFieldsFilterset):
    facility = filters.AllValuesFilter(lookup_expr='exact')
    comment = filters.CharFilter(lookup_expr='icontains')
    is_cancelled = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityApproval


class ServiceCategoryFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = ServiceCategory


class OptionFilter(CommonFieldsFilterset):
    value = filters.CharFilter(lookup_expr='icontains')
    display_text = filters.CharFilter(lookup_expr='icontains')
    option_type = filters.CharFilter(lookup_expr='icontains')
    is_exclusive_option = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = Option


class ServiceFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    category = filters.AllValuesFilter(lookup_expr='exact')
    code = filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Service


class FacilityServiceFilter(CommonFieldsFilterset):
    facility = filters.AllValuesFilter(lookup_expr='exact')
    option = filters.AllValuesFilter(lookup_expr='exact')
    is_confirmed = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )
    is_cancelled = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityService


class OwnerTypeFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = OwnerType


class OwnerFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    abbreviation = filters.CharFilter(lookup_expr='icontains')
    code = filters.NumberFilter(lookup_expr='exact')
    owner_type = filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Owner


class JobTitleFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = JobTitle


class OfficerContactFilter(CommonFieldsFilterset):
    officer = filters.AllValuesFilter(lookup_expr='exact')
    contact = filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = OfficerContact


class OfficerFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    registration_number = filters.CharFilter(lookup_expr='icontains')
    job_title = filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Officer


class FacilityStatusFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityStatus


class FacilityAdmissionStatusFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityAdmissionStatus


class RegulatingBodyFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    abbreviation = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = RegulatingBody


class RegulationStatusFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = RegulationStatus


class FacilityRegulationStatusFilter(CommonFieldsFilterset):
    facility = filters.AllValuesFilter(lookup_expr='exact')
    regulating_body = filters.AllValuesFilter(lookup_expr='exact')
    regulation_status = filters.AllValuesFilter(lookup_expr='exact')
    reason = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityRegulationStatus


class FacilityContactFilter(CommonFieldsFilterset):
    facility = django_filters.CharFilter(lookup_expr='exact')
    contact = django_filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityContact


class FacilityFilter(CommonFieldsFilterset):
    """
    FilterSet for the Facility model, compatible with django-filter version 23.5.
    Allows filtering on various fields including foreign keys, boolean fields, and text fields.
    """
    BooleanFilter = lambda **kwargs: filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=lambda v: bool(strtobool(v)), **kwargs
    )

    def service_filter(self, qs, name, value):
        services = value.split(',')
        facility_ids = []

        for facility in qs.filter():
            for _service in services:
                service_count = FacilityService.objects.filter(
                    service=_service,
                    facility=facility).count()
                if service_count > 0:
                    facility_ids.append(facility.id)

        return qs.filter(id__in=list(set(facility_ids)))

    def infrastructure_filter(self, qs, name, value):
        infrastructure = value.split(',')
        facility_ids = []

        for facility in qs.filter():
            for _infra in infrastructure:
                infrastructure_count = FacilityInfrastructure.objects.filter(
                    infrastructure=_infra,
                    facility=facility).count()
                if infrastructure_count > 0:
                    facility_ids.append(facility.id)

        return qs.filter(id__in=list(set(facility_ids)))

    def hr_filter(self, qs, name, value):
        specialities = value.split(',')
        facility_ids = []

        for facility in qs.filter():
            for _speciality in specialities:
                speciality_count = FacilitySpecialist.objects.filter(
                    speciality=_speciality,
                    facility=facility).count()
                if speciality_count > 0:
                    facility_ids.append(facility.id)

        return qs.filter(id__in=list(set(facility_ids)))

    def filter_approved_facilities(self, qs, name, value):

        if value in TRUTH_NESS:
            return qs.filter(Q(approved=True))
        else:
            return qs.filter(Q(approved=None) | Q(rejected=True))

    def filter_facilities_with_pending_updates(self, qs, name, value):

        if value in TRUTH_NESS:
            facilities_pending_updates = qs.filter(has_edits=True)

            facilities_latest_updates_ids = [f.id for f in facilities_pending_updates if f.latest_update is None]

            return facilities_pending_updates.exclude(id__in=facilities_latest_updates_ids)

    def filter_unpublished_facilities_national_level(self, qs, name, value):
        """
        This is in order to allow the facilities to be seen
        so that they can be approved at the national level and assigned an MFL code.
        """

        if value in TRUTH_NESS:
            pending_approval_qs = qs.filter(
                Q(Q(approved_national_level=None) | Q(approved_national_level=False)),
                approved=True,
                has_edits=False,
                closed=False,
                rejected=False,
                code=None
            )

            incomplete_pending_approval_ids = [facility.id for facility in pending_approval_qs if
                                               not facility.is_complete]

            return pending_approval_qs.exclude(id__in=incomplete_pending_approval_ids)

        else:
            approved_qs = qs.filter(
                approved_national_level=True, approved=True, has_edits=False, closed=False, rejected=False
            )

            incomplete_approved_qs = [facility.id for facility in approved_qs if not facility.is_complete]

            return approved_qs.exclude(id__in=incomplete_approved_qs)

    def filter_incomplete_facilities(self, qs, name, value):
        """
        Filter the incomplete/complete facilities
        """

        all_facilities = qs.all()
        if value in TRUTH_NESS:
            complete_facilities_ids = [facility.id for facility in all_facilities if facility.is_complete]
            return all_facilities.exclude(id__in=complete_facilities_ids)
        else:
            incomplete_facilities_ids = [facility.id for facility in all_facilities if not facility.is_complete]
            return all_facilities.exclude(id__in=incomplete_facilities_ids)

    def facilities_pending_approval(self, qs, name, value):

        if value in TRUTH_NESS:
            pending_validation_qs = qs.filter(
                has_edits=False,
                approved=None,
                rejected=False,
                approved_national_level=None,
                code=None
            )

            incomplete_pending_validation_ids = [facility.id for facility in pending_validation_qs if
                                                 not facility.is_complete]

            return pending_validation_qs.exclude(id__in=incomplete_pending_validation_ids)
        else:
            validated_qs = qs.filter(
                rejected=False,
                has_edits=False,
                approved=True,
                approved_national_level=None
            )

            incomplete_validated_ids = [facility.id for facility in validated_qs if not facility.is_complete]

            return validated_qs.exclude(id__in=incomplete_validated_ids)

    def filter_national_rejected(self, qs, name, value):
        rejected_national = qs.filter(rejected=False, code=None,
                                      approved=True, approved_national_level=False)
        if value in TRUTH_NESS:
            return rejected_national
        else:
            return qs.exclude(id__in=[facility.id for facility in rejected_national])

    def filter_number_beds(self, qs, name, value):
        return qs.filter(number_of_beds__gte=1)

    def filter_number_cots(self, qs, name, value):
        return qs.filter(number_of_cots__gte=1)

    id = filters.CharFilter(lookup_expr='exact')
    name = filters.CharFilter(lookup_expr='icontains',
                              help_text='Filter by facility name (case-insensitive contains)')
    official_name = filters.CharFilter(lookup_expr='icontains',
                                       help_text='Filter by official name (case-insensitive contains)')
    code = filters.CharFilter(lookup_expr='exact', help_text='Filter by exact facility code')
    description = filters.CharFilter(lookup_expr='icontains')
    registration_number = filters.CharFilter(lookup_expr='exact',
                                             help_text='Filter by exact registration number')  # not there in v2
    abbreviation = filters.CharFilter(lookup_expr='icontains',
                                      help_text='Filter by abbreviation (case-insensitive contains)')
    # With foreign Keys
    facility_type = ListUUIDFilter(field_name='facility_type__id', lookup_expr='in')
    operation_status = ListUUIDFilter(field_name='operation_status__id', lookup_expr='in')
    regulatory_body = ListUUIDFilter(field_name='regulatory_body__id', lookup_expr='in')
    keph_level = ListUUIDFilter(field_name='keph_level__id', lookup_expr='in')
    regulation_status = ListUUIDFilter(field_name='regulation_status__id',
                                       help_text='Filter by regulation status')
    officer_in_charge = ListUUIDFilter(field_name='officer_in_charge__id',
                                       help_text='Filter by officer in charge')
    admission_status = ListUUIDFilter(field_name='admission_status__id',
                                      help_text='Filter by admission status')  # not there in v2
    owner = ListUUIDFilter(field_name='owner__id', lookup_expr='in', help_text='Filter by owner id')
    owner_type = ListUUIDFilter(field_name='owner__owner_type__id', lookup_expr='in', help_text='Filter by owner type')
    county = ListUUIDFilter(field_name='ward__sub_county__county__id', help_text='Filter by county id')
    sub_county = ListUUIDFilter(field_name='ward__sub_county__id', help_text='Filter by sub-county id')
    ward = ListUUIDFilter(field_name='ward__id', help_text='Filter by ward id', lookup_expr='in')
    county_code = ListUUIDFilter(field_name='ward__sub_county__county__code', help_text='Filter by county code')
    sub_county_code = ListUUIDFilter(field_name='ward__sub_county__code', help_text='Filter by sub-county code')
    ward_code = ListUUIDFilter(field_name='ward__code', help_text='Filter by ward code', lookup_expr='in')

    # Boolean filters
    open_whole_day = BooleanFilter(help_text='Filter by facilities open 24 hours')
    open_public_holidays = BooleanFilter(help_text='Filter by facilities open on public holidays')
    open_normal_day = BooleanFilter(help_text='Filter by facilities open 8am-5pm')  # not there in v2
    open_weekends = BooleanFilter(help_text='Filter by facilities open on weekends')
    open_late_night = BooleanFilter(help_text='Filter by facilities open late night')
    is_classified = BooleanFilter(help_text='Filter by classified facilities')
    is_published = BooleanFilter(help_text='Filter by published facilities')
    accredited_lab_iso_15189 = BooleanFilter(help_text='Filter by ISO 15189 accredited labs')
    regulated = BooleanFilter(help_text='Filter by regulated facilities')
    rejected = BooleanFilter(help_text='Filter by rejected facilities')
    has_edits = BooleanFilter(help_text='Filter by facilities with pending edits')
    closed = BooleanFilter(help_text='Filter by closed facilities')
    reporting_in_dhis = BooleanFilter(help_text='Filter by facilities reporting in DHIS')
    nhif_accreditation = BooleanFilter(help_text='Filter by NHIF accredited facilities')
    approved_national_level = BooleanFilter(help_text='Filter by nationally approved facilities')

    # Numeric filters
    number_of_emergency_casualty_beds = filters.RangeFilter(field_name='number_of_emergency_casualty_beds',
                                                            help_text='Filter by range of emergency casualty beds')
    number_of_icu_beds = filters.RangeFilter(field_name='number_of_icu_beds', help_text='Filter by range of ICU beds')
    number_of_hdu_beds = filters.RangeFilter(field_name='number_of_hdu_beds', help_text='Filter by range of HDU beds')
    number_of_inpatient_beds = filters.RangeFilter(field_name='number_of_inpatient_beds',
                                                   help_text='Filter by range of inpatient beds')

    number_of_maternity_beds = filters.RangeFilter(field_name='number_of_maternity_beds',
                                                   help_text='Filter by range of maternity beds')
    number_of_isolation_beds = filters.RangeFilter(field_name='number_of_isolation_beds',
                                                   help_text='Filter by range of isolation beds')
    number_of_general_theatres = filters.RangeFilter(field_name='number_of_general_theatres',
                                                     help_text='Filter by range of general theatres')
    number_of_maternity_theatres = filters.RangeFilter(field_name='number_of_maternity_theatres',
                                                       help_text='Filter by range of maternity theatres')
    number_of_minor_theatres = filters.RangeFilter(field_name='number_of_minor_theatres',
                                                   help_text='Filter by range of minor theatres')
    number_of_eye_theatres = filters.RangeFilter(field_name='number_of_eye_theatres',
                                                 help_text='Filter by range of eye theatres')
    facility_catchment_population = filters.RangeFilter(field_name='facility_catchment_population',
                                                        help_text='Filter by range of catchment population')

    # Date filters not in v2
    closed_date = filters.DateFromToRangeFilter(field_name='closed_date', help_text='Filter by range of closing date')
    approvalrejection_date = filters.DateFromToRangeFilter(field_name='approvalrejection_date',
                                                           help_text='Filter by range of approval/rejection date')
    date_established = filters.DateFromToRangeFilter(field_name='date_established',
                                                     help_text='Filter by range of establishment date')
    # Method filters
    pending_approval = filters.CharFilter(
        method='facilities_pending_approval')

    is_approved = filters.CharFilter(
        method='filter_approved_facilities')

    service = filters.CharFilter(
        method=service_filter)
    infrastructure = filters.CharFilter(
        method='infrastructure_filter')
    speciality = filters.CharFilter(
        method='hr_filter')
    rejected_national = filters.CharFilter(
        method='filter_national_rejected')
    search = ClassicSearchFilter(field_name='official_name')  # name='name'
    incomplete = filters.CharFilter(
        method='filter_incomplete_facilities')
    to_publish = filters.CharFilter(
        method='filter_unpublished_facilities_national_level')
    have_updates = filters.CharFilter(
        method='filter_facilities_with_pending_updates')
    number_of_beds = filters.CharFilter(method='filter_number_beds')
    number_of_cots = filters.CharFilter(method='filter_number_cots')

    class Meta:
        model = Facility
        fields = [
            'name', 'official_name', 'code', 'registration_number', 'abbreviation',
            'facility_type', 'operation_status', 'regulatory_body', 'keph_level',
            'county', 'sub_county', 'ward', 'owner', 'regulation_status', 'admission_status',
            'open_whole_day', 'open_public_holidays', 'open_normal_day', 'open_weekends',
            'open_late_night', 'is_classified', 'is_published', 'accredited_lab_iso_15189',
            'regulated', 'approved', 'rejected', 'has_edits', 'closed', 'reporting_in_dhis',
            'nhif_accreditation', 'approved_national_level', 'number_of_beds', 'number_of_cots',
            'number_of_emergency_casualty_beds', 'number_of_icu_beds', 'number_of_hdu_beds',
            'number_of_inpatient_beds', 'number_of_maternity_beds', 'number_of_isolation_beds',
            'number_of_general_theatres', 'number_of_maternity_theatres', 'number_of_minor_theatres',
            'number_of_eye_theatres', 'facility_catchment_population', 'closed_date',
            'approvalrejection_date', 'date_established'
        ]


class FacilityTypeFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    sub_division = filters.CharFilter(lookup_expr='icontains')
    is_parent = NullFilter(field_name='parent')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityType


class FacilityUnitFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    facility = filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityUnit


class FacilityUnitRegulationFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityUnitRegulation


class FacilityDepartmentFilter(CommonFieldsFilterset):
    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityDepartment


# Speciality filters

class SpecialityCategoryFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = SpecialityCategory


class SpecialityFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    category = filters.AllValuesFilter(lookup_expr='exact')
    code = filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Speciality


class FacilitySpecialistFilter(CommonFieldsFilterset):
    facility = filters.AllValuesFilter(lookup_expr='exact')
    speciality = filters.AllValuesFilter(lookup_expr='exact')
    is_confirmed = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES
    )
    is_cancelled = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES
    )

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilitySpecialist


# Infrastructure

class InfrastructureCategoryFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = InfrastructureCategory


class InfrastructureFilter(CommonFieldsFilterset):
    name = filters.CharFilter(lookup_expr='icontains')
    description = filters.CharFilter(lookup_expr='icontains')
    category = filters.AllValuesFilter(lookup_expr='exact')
    code = filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Infrastructure


class FacilityInfrastructureFilter(CommonFieldsFilterset):
    facility = filters.AllValuesFilter(lookup_expr='exact')
    infrastructure = filters.AllValuesFilter(lookup_expr='exact')
    is_confirmed = filters.TypedChoiceFilter(choices=BOOLEAN_CHOICES)
    is_cancelled = filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES
    )

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityInfrastructure
