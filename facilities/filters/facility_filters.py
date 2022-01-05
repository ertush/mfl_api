from django.db.models import Q

from distutils.util import strtobool
import django_filters



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
from common.filters.filter_shared import (
    CommonFieldsFilterset,
    ListIntegerFilter,
    ListCharFilter,
    NullFilter,
    ListUUIDFilter
)

from search.filters import ClassicSearchFilter

from common.constants import BOOLEAN_CHOICES, TRUTH_NESS


class FacilityExportExcelMaterialViewFilter(django_filters.FilterSet):

    def filter_number_beds(self, qs, name, value):
        return qs.filter(beds__gte=1)

    def filter_number_cots(self, qs, name, value):
        return qs.filter(cots__gte=1)

    search = ClassicSearchFilter(name='search')
    county = ListCharFilter(lookup_expr='exact')
    code = ListCharFilter(lookup_expr='exact')
    constituency = ListCharFilter(lookup_expr='exact')
    ward = ListCharFilter(lookup_expr='exact')
    owner = ListCharFilter(lookup_expr='exact')
    owner_type = ListCharFilter(lookup_expr='exact')
    number_of_beds = django_filters.CharFilter(method='filter_number_beds')
    number_of_cots = django_filters.CharFilter(method='filter_number_cots')
    open_whole_day = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_late_night = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_weekends = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_public_holidays = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    keph_level = ListCharFilter(lookup_expr='exact')
    facility_type = ListCharFilter(lookup_expr='exact')
    operation_status = ListCharFilter(lookup_expr='exact')
    service = ListUUIDFilter(lookup_expr='exact', name='services')
    service_category = ListUUIDFilter(lookup_expr='exact', name='categories')
    service_name = ClassicSearchFilter(name='service_names')
    approved_national_level = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityExportExcelMaterialView
        exclude = ('services', 'categories', 'service_names', )


class RegulatorSyncFilter(CommonFieldsFilterset):
    mfl_code_null = NullFilter(name='mfl_code')
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
    facility = django_filters.AllValuesFilter(
        name='facility_service__facility',
        lookup_expr='exact')
    service = django_filters.AllValuesFilter(
        name="facility_service__service", lookup_expr='exact')
    county = django_filters.AllValuesFilter(
        name="facility_service__facility__ward__constituency__county",
        lookup_expr='exact')
    constituency = django_filters.AllValuesFilter(
        name="facility_service__facility__ward__constituency",
        lookup_expr='exact')
    ward = django_filters.AllValuesFilter(
        name="facility_service__facility__ward", lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityServiceRating


class RegulatingBodyContactFilter(CommonFieldsFilterset):

    class Meta(CommonFieldsFilterset.Meta):
        model = RegulatingBodyContact


class FacilityUpgradeFilter(CommonFieldsFilterset):
    is_confirmed = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    is_cancelled = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityUpgrade


class FacilityOperationStateFilter(CommonFieldsFilterset):
    operation_status = django_filters.AllValuesFilter(lookup_expr='exact')
    facility = django_filters.AllValuesFilter(lookup_expr='exact')
    reason = django_filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityOperationState


class FacilityApprovalFilter(CommonFieldsFilterset):
    facility = django_filters.AllValuesFilter(lookup_expr='exact')
    comment = django_filters.CharFilter(lookup_expr='icontains')
    is_cancelled = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityApproval


class ServiceCategoryFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = ServiceCategory


class OptionFilter(CommonFieldsFilterset):
    value = django_filters.CharFilter(lookup_expr='icontains')
    display_text = django_filters.CharFilter(lookup_expr='icontains')
    option_type = django_filters.CharFilter(lookup_expr='icontains')
    is_exclusive_option = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = Option


class ServiceFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.AllValuesFilter(lookup_expr='exact')
    code = django_filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Service


class FacilityServiceFilter(CommonFieldsFilterset):
    facility = django_filters.AllValuesFilter(lookup_expr='exact')
    option = django_filters.AllValuesFilter(lookup_expr='exact')
    is_confirmed = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )
    is_cancelled = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityService


class OwnerTypeFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = OwnerType


class OwnerFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    abbreviation = django_filters.CharFilter(lookup_expr='icontains')
    code = django_filters.NumberFilter(lookup_expr='exact')
    owner_type = django_filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Owner


class JobTitleFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = JobTitle


class OfficerContactFilter(CommonFieldsFilterset):
    officer = django_filters.AllValuesFilter(lookup_expr='exact')
    contact = django_filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = OfficerContact


class OfficerFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    registration_number = django_filters.CharFilter(lookup_expr='icontains')
    job_title = django_filters.AllValuesFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Officer


class FacilityStatusFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityStatus
class FacilityAdmissionStatusFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityAdmissionStatus


class FacilityTypeFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    sub_division = django_filters.CharFilter(lookup_expr='icontains')
    is_parent = NullFilter(name='parent')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityType


class RegulatingBodyFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    abbreviation = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = RegulatingBody


class RegulationStatusFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = RegulationStatus


class FacilityRegulationStatusFilter(CommonFieldsFilterset):
    facility = django_filters.AllValuesFilter(lookup_expr='exact')
    regulating_body = django_filters.AllValuesFilter(lookup_expr='exact')
    regulation_status = django_filters.AllValuesFilter(lookup_expr='exact')
    reason = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityRegulationStatus


class FacilityContactFilter(CommonFieldsFilterset):
    facility = django_filters.CharFilter(lookup_expr='exact')
    contact = django_filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityContact


class FacilityFilter(CommonFieldsFilterset):

    def service_filter(self, qs, name, value):
        categories = value.split(',')
        facility_ids = []

        for facility in self.filter():
            for cat in categories:
                service_count = FacilityService.objects.filter(
                    service__category=cat,
                    facility=facility).count()
                if service_count > 0:
                    facility_ids.append(facility.id)

        return qs.filter(id__in=list(set(facility_ids)))

    def filter_approved_facilities(self, qs, name, value):

        if value in TRUTH_NESS:
            return qs.filter(Q(approved=True) | Q(rejected=True))
        else:
            return qs.filter(rejected=False, approved=False)

    def filter_unpublished_facilities_national_level(self, qs, name, value):
        """
        This is in order to allow the facilities to be seen
        so that they can be approved at the national level and assigned an MFL code.
        """
        return qs.filter(
            approved_national_level=None, code=None, approved=True, has_edits=False,closed=False
        )

    def filter_incomplete_facilities(self, qs, name, value):
        """
        Filter the incomplete/complete facilities
        """
        incomplete = qs.filter(code=None)
        if value in TRUTH_NESS:
            return incomplete
        else:
            return qs.exclude(id__in=[facility.id for facility in incomplete])

    def facilities_pending_approval(self, qs, name, value):
        fac_pend_appr = qs.filter(code=not None)
        fac_pend_appr_facility_ids = [facility.id for facility in fac_pend_appr]
        if value in TRUTH_NESS:
            return qs.filter(
                Q(
                    Q(rejected=False),
                    Q(has_edits=True) |
                    Q(approved=None,rejected=False)
                ) |
                Q(
                    Q(rejected=False),
                    Q(has_edits=True) | Q(approved=None,rejected=False))
            ).exclude(id__in=fac_pend_appr_facility_ids)
        else:
            return qs.filter(
                Q(rejected=True) |
                Q(has_edits=False) & Q(approved=None)
            ).exclude(id__in=fac_pend_appr_facility_ids)

    def filter_national_rejected(self, qs, name, value):
        rejected_national = qs.filter(rejected=False,code=None,
            approved=True,approved_national_level=False)
        if value in TRUTH_NESS:
            return rejected_national
        else:
            return qs.exclude(id__in=[facility.id for facility in rejected_national])


    def filter_number_beds(self, qs, name, value):
        return qs.filter(number_of_beds__gte=1)

    def filter_number_cots(self, qs, name, value):
        return self.filter(number_of_cots__gte=1)

    id = ListCharFilter(lookup_expr='icontains')
    name = django_filters.CharFilter(lookup_expr='icontains')
    code = ListIntegerFilter(lookup_expr='exact')
    description = ListCharFilter(lookup_expr='icontains')

    facility_type = ListCharFilter(lookup_expr='icontains')
    keph_level = ListCharFilter(lookup_expr='exact')
    operation_status = ListCharFilter(lookup_expr='icontains')
    ward = ListCharFilter(lookup_expr='icontains')
    sub_county = ListCharFilter(lookup_expr='exact', name='ward__sub_county')
    sub_county_code = ListCharFilter(
        name="ward__sub_county__code", lookup_expr='exact')
    ward_code = ListCharFilter(name="ward__code", lookup_expr='icontains')
    county_code = ListCharFilter(
        name='ward__constituency__county__code',
        lookup_expr='icontains')
    constituency_code = ListCharFilter(
        name='ward__constituency__code', lookup_expr='icontains')
    county = ListCharFilter(
        name='ward__constituency__county',
        lookup_expr='exact')
    constituency = ListCharFilter(
        name='ward__constituency', lookup_expr='icontains')
    owner = ListCharFilter(lookup_expr='icontains')
    owner_type = ListCharFilter(name='owner__owner_type', lookup_expr='exact')
    officer_in_charge = ListCharFilter(lookup_expr='icontains')
    number_of_beds = django_filters.CharFilter(method='filter_number_beds')
    number_of_cots = django_filters.CharFilter(method='filter_number_cots')
    open_whole_day = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_late_night = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_weekends = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    open_public_holidays = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    is_classified = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    is_published = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    is_approved = django_filters.CharFilter(
        method='filter_approved_facilities')
    service_category = django_filters.CharFilter(
        method=service_filter)
    has_edits = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    rejected = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    regulated = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    approved = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    closed = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool)
    pending_approval = django_filters.CharFilter(
        method='facilities_pending_approval')
    rejected_national = django_filters.CharFilter(
        method='filter_national_rejected')
    search = ClassicSearchFilter(name='name')
    incomplete = django_filters.CharFilter(
        method='filter_incomplete_facilities')
    to_publish = django_filters.CharFilter(
        method='filter_unpublished_facilities_national_level')
    approved_national_level = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)
    reporting_in_dhis = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES,
        coerce=strtobool)

    class Meta(CommonFieldsFilterset.Meta):
        model = Facility


class FacilityUnitFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    facility = django_filters.CharFilter(lookup_expr='exact')

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
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = SpecialityCategory

class SpecialityFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.AllValuesFilter(lookup_expr='exact')
    code = django_filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Speciality

class FacilitySpecialistFilter(CommonFieldsFilterset):
    facility = django_filters.AllValuesFilter(lookup_expr='exact')
    speciality = django_filters.AllValuesFilter(lookup_expr='exact')
    is_confirmed = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )
    is_cancelled = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilitySpecialist

# Infrastructure

class InfrastructureCategoryFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')

    class Meta(CommonFieldsFilterset.Meta):
        model = InfrastructureCategory

class InfrastructureFilter(CommonFieldsFilterset):
    name = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    category = django_filters.AllValuesFilter(lookup_expr='exact')
    code = django_filters.CharFilter(lookup_expr='exact')

    class Meta(CommonFieldsFilterset.Meta):
        model = Infrastructure

class FacilityInfrastructureFilter(CommonFieldsFilterset):
    facility = django_filters.AllValuesFilter(lookup_expr='exact')
    infrastructure = django_filters.AllValuesFilter(lookup_expr='exact')
    is_confirmed = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )
    is_cancelled = django_filters.TypedChoiceFilter(
        choices=BOOLEAN_CHOICES, coerce=strtobool
    )

    class Meta(CommonFieldsFilterset.Meta):
        model = FacilityInfrastructure