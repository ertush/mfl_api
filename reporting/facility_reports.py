import functools
import json
import uuid

from datetime import timedelta
from collections import OrderedDict, defaultdict
from django.apps import apps
from django.db.models import Sum, Case, When, IntegerField, Count, ExpressionWrapper, Q, F, Value, FloatField, Func, \
    TextField, Subquery
from django.utils import timezone
from django.core.paginator import Paginator

from rest_framework.views import APIView, Response
from rest_framework.exceptions import NotFound, ValidationError

from facilities.models import (
    Facility,ServiceCategory,
    FacilityType,InfrastructureCategory,
    KephLevel, Speciality, FacilitySpecialist,SpecialityCategory,
    FacilityUpgrade, OwnerType, Owner, RegulatingBody, Service, FacilityInfrastructure, FacilityService, Infrastructure)
from common.constants import TRUTH_NESS, FALSE_NESS
from common.models import (
    County, Constituency, Ward, SubCounty
)
from chul.models import CommunityHealthUnit, Status, CHUService, CHUServiceLink
from mfl_gis.models import FacilityCoordinates

from .report_config import REPORTS


class FilterReportMixin(object):
    queryset = Facility.objects.all()

    def _prepare_filters(self, filtering_data):
        filtering_data = filtering_data.split('=')
        return filtering_data[0], filtering_data[1]

    def _build_dict_filter(self, filter_field_name, value):
        return {
            filter_field_name: value
        }

    def _filter_queryset(self, filter_dict):
        return self.queryset.filter(**filter_dict)

    def _filter_relation_obj(self, model, field_name, value):
        filter_dict = {
            field_name: value
        }
        return model.objects.filter(**filter_dict)

    def _filter_by_extra_params(
            self, report_config, more_filters_params, model):
        more_filters = self._prepare_filters(more_filters_params)

        requested_filters = report_config.get(
            'extra_filters')[more_filters[0]]
        requested_filters_filter_field_name = requested_filters.get(
            'filter_field_name')
        filtering_dict = self._build_dict_filter(
            requested_filters_filter_field_name, more_filters[1])

        self.queryset = self._filter_queryset(filtering_dict)
        model_instances = self._filter_relation_obj(
            model, more_filters[0], more_filters[1])
        return model_instances

    def _get_return_data(
            self, filter_field_name, model_instances, return_instance_name,
            return_count_name):
        data = []

        for instance in model_instances:
            filiter_data = {
                filter_field_name: instance
            }
            count = self.queryset.filter(**filiter_data).count()
            instance_name = instance.name
            data.append(
                {
                    return_instance_name: instance_name,
                    return_count_name: count
                }
            )
        return data

    def _get_user_top_level(self):
        userid = self.request.user.groups.all()[0].id
        groupby = self.request.query_params.get('report_groupby', '')
        resultobject = {'usertoplevel': '', 'userlowerlevels': [], 'usergroupby': 'sub_county'}
        resultobject['userlowerlevels'].append('ward')
        if userid == 5 or userid==6 or userid==7:
            resultobject['usertoplevel'] = 'national'
            resultobject['userlowerlevels'].append('national')
            if (groupby == 'county' or groupby == 'sub_county' or groupby == 'ward'):
                resultobject['usergroupby'] = groupby
            else:
                resultobject['usergroupby'] = 'county'
            return resultobject
        elif userid == 1 or userid==12:
            resultobject['usertoplevel'] = 'county'
            resultobject['userlowerlevels'].append('county')
            if (groupby == 'county' or groupby == 'sub_county' or groupby == 'ward'):
                resultobject['usergroupby'] = groupby
            else:
                resultobject['usergroupby'] = 'county'
            return resultobject
        elif userid == 2:
            resultobject['usertoplevel'] = 'sub_county'
            resultobject['userlowerlevels'].append('sub_county')
            if (groupby == 'county' or groupby == 'sub_county' or groupby == 'ward'):
                resultobject['usergroupby'] = groupby
            else:
                resultobject['usergroupby'] = 'sub_county'
            return resultobject
        else:
            resultobject['usergroupby'] = groupby
            return resultobject

    def get_report_data(self, *args, **kwargs):
        '''Route reports based on report_type param.'''
        report_type = self.request.query_params.get(
            'report_type', 'facility_count_by_county')
        report_groupby = self.request.query_params.get(
            'report_groupby', '')
        if report_type == 'facility_count_by_facility_type_detailed':
            return self._get_facility_type_data()

        if report_type == 'facility_count_by_county':
            return self._get_facility_count_by_county()

        if report_type == 'facility_keph_level_report':
            return self._get_facility_count(keph=True)

        # New facility report Facility
        if report_type == 'facility_report_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_facility_report_all_hierachies(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)

        # New facility multi report
        if report_type == 'all_facility_details':

            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_all_facility_details(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)

        # New report format keph levels
        if report_type == 'facility_keph_level_report_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}
            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_facility_count_keph_level(vals={
                'ward__sub_county__county__name': 'county_name',
                'ward__sub_county__county': 'county',
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)

        # New report Format regulatory body
        if report_type == 'facility_regulatory_body_report_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_facility_count_regulatory_body(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)

        # New report Format Facility Type
        if report_type == 'facility_type_report_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_facility_count_facility_type(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)

        # New report Format Facility services and service category
        if report_type == 'facility_services_report_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['facility__ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['facility__ward__sub_county__id'] = constituency_id

            return self._get_facility_services(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)

        # New report Format Facility infrastructure and infrastructure category
        if report_type == 'facility_infrastructure_report_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_facility_infrustructure(vals={
                'facility__ward__sub_county__name': 'sub_county_name',
                'facility__ward__sub_county': 'sub_county',
                'facility__ward__name': 'ward_name',
                'facility__ward': 'ward'
            }, filters=filters)

        # New report format for facility human resource category

        if report_type == 'facility_human_resource_category_report_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_facility_humanresource(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)


        # New report Format facility owner
        if report_type == 'facility_owner_report_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_facility_count_owner(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)

        if report_type == 'facility_count_by_sub_county':
            return self._get_facility_sub_county_data()

        if report_type == 'individual_facility_beds_and_cots':
            return self._get_facilities_beds_and_cots()

        if report_type == 'facility_count_by_owner_category':
            return self._get_facility_count(category=True)

        if report_type == 'facility_count_by_owner':
            return self._get_facility_count(category=False)

        if report_type == 'facility_count_by_facility_type':
            return self._get_facility_count_by_facility_type()

        if report_type == 'facility_count_by_facility_type_details':
            return self._get_facility_count_by_facility_type_details()

        if report_type == 'gis':
            return self._get_gis_report()

        if report_type == 'facility_nhif_accreditation':
            return self._get_nhif_accreditation()

        # New Report format (beds and cots filter)
        if report_type == 'beds_and_cots_by_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id

            return self._get_beds_and_cots_all_hierachies(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county',
                'ward__name': 'ward_name',
                'ward': 'ward'
            }, filters=filters)

        if report_type == 'beds_and_cots_by_county':
            return self._get_beds_and_cots({
                'ward__sub_county__county__name': 'county_name',
                'ward__sub_county__county': 'county'
            })

        if report_type == 'beds_and_cots_by_constituency':
            county_id = self.request.query_params.get('county', None)
            filters = (
                {} if county_id is None
                else {'ward__sub_county__county': county_id}
            )
            return self._get_beds_and_cots(vals={
                'ward__sub_county__name': 'sub_county_name',
                'ward__sub_county': 'sub_county'
            }, filters=filters)

        if report_type == 'beds_and_cots_by_ward':
            constituency_id = self.request.query_params.get(
                'constituency', None
            )
            filters = (
                {} if constituency_id is None
                else {'ward__sub_county': constituency_id}
            )
            return self._get_beds_and_cots(
                vals={'ward__name': 'ward_name', 'ward': 'ward'},
                filters=filters
            )

        if report_type == 'beds_and_cots_by_keph_level':
            keph_level_id = self.request.query_params.get(
                'keph_level', None
            )
            filters = (
                {} if keph_level_id is None
                else {'keph_level': keph_level_id}
            )

            return self._get_beds_and_cots(
                vals={'keph_level__name': 'keph_level_name', 'keph_level_id': 'keph_level'},
                filters=filters
            )

        if report_type == 'beds_and_cots_by_owner':
            keph_level_id = self.request.query_params.get(
                'owner', None
            )
            filters = (
                {} if keph_level_id is None
                else {'owner': keph_level_id}
            )

            return self._get_beds_and_cots(
                vals={'owner__name': 'owner_name', 'owner_id': 'owner'},
                filters=filters
            )

        more_filters_params = self.request.query_params.get('filters', None)

        report_config = REPORTS.get(report_type, None)
        if report_config is None:
            raise NotFound(detail='Report not found.')

        group_by = report_config.get('group_by')
        app_label, model_name = report_config.get(
            'filter_fields').get('model').split('.')
        filter_field_name = report_config.get(
            'filter_fields').get('filter_field_name')
        model = apps.get_model(app_label, model_name)
        model_instances = model.objects.all()

        if more_filters_params:
            model_instances = self._filter_by_extra_params(
                report_config, more_filters_params, model)

        return_instance_name = report_config.get(
            'filter_fields').get('return_field')[0]
        return_count_name = report_config.get(
            'filter_fields').get('return_field')[1]
        if group_by:
            pass
        else:
            data = self._get_return_data(
                filter_field_name, model_instances, return_instance_name,
                return_count_name)
        return data, self.queryset.count()

    def _get_facility_type_data(self):
        owner_category = self.request.query_params.get('owner_category')
        facility_type = self.request.query_params.get('facility_type')

        data = []

        for county in County.objects.all():
            for facility_type in FacilityType.objects.all():
                if not owner_category:
                    count = Facility.objects.filter(
                        facility_type=facility_type,
                        ward__constituency__county=county).count()
                else:
                    count = Facility.objects.filter(
                        facility_type=facility_type,
                        ward__constituency__county=county,
                        owner__owner_type=owner_category).count()

                data.append(
                    {
                        'county': county.name,
                        'facility_type': facility_type.name,
                        'number_of_facilities': count
                    }
                )

        totals = []

        return data, totals

    def _get_facility_keph_level_data(self):
        owner_category = self.request.query_params.get('owner_category')

        data = []

        for county in County.objects.all():
            for level in KephLevel.objects.all():
                if not owner_category:
                    count = Facility.objects.filter(
                        keph_level=level,
                        ward__constituency__county=county).count()
                else:
                    count = Facility.objects.filter(
                        level=level,
                        ward__constituency__county=county,
                        owner__owner_type=owner_category).count()

                data.append({
                    'county': county.name,
                    # 'sub county':'sample sub county',
                    # 'ward':'sample ward',
                    # 'level 1':'leavel 1',
                    # 'level 1':'leavel 2',
                    # 'level 1':'leavel 3',
                    # 'level 1':'leavel 4',
                    # 'level 1':'leavel 5',
                    # 'level 1':'leavel 1',

                    'keph_level': level.name,
                    'number_of_facilities': count
                })

        totals = []
        return data, totals

    def _get_facility_constituency_data(self):
        owner_category = self.request.query_params.get('owner_category')

        data = []

        for county in County.objects.all():
            for const in Constituency.objects.filter(county=county):
                if not owner_category:
                    count = Facility.objects.filter(
                        ward__constituency=const).count()
                else:
                    count = Facility.objects.filter(
                        ward__constituency=const,
                        owner__owner_type=owner_category).count()

                data.append({
                    'county': county.name,
                    'constituency': const.name,
                    'number_of_facilities': count
                })

            totals = []
        return data, totals

    def _get_facility_sub_county_data(self):
        report_level = self.request.query_params.get('report_level', None)
        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)

        data = []
        totals = []
        if report_level == 'national':

            for county in County.objects.all():
                count = Facility.objects.filter(
                    ward__sub_county__county=county).count()
                data_dict = {
                    'number_of_facilities': count,
                    'county_id': str(county.id),
                    'county': county.name,
                }
                data.append(data_dict)

        if report_level == 'county':
            for sub_county in SubCounty.objects.filter(
                    county_id__in=county.split(',')):
                count = Facility.objects.filter(
                    ward__sub_county=sub_county).count()
                data_dict = {
                    'number_of_facilities': count,
                    'sub_county_id': str(sub_county.id),
                    'sub_county': sub_county.name,
                }
                data.append(data_dict)

        if report_level == 'sub_county':
            for ward in Ward.objects.filter(
                    sub_county_id__in=sub_county.split(',')):
                count = Facility.objects.filter(
                    ward=ward).count()
                data_dict = {
                    'number_of_facilities': count,
                    'ward': ward.name,
                    'ward_id': str(ward.id)
                }
                data.append(data_dict)

        return data, totals

    def _get_facilities_beds_and_cots(self):
        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)
        data = []
        queryset_filter = {}
        if county:
            county = County.objects.get(id=county)
            queryset_filter = {
                'ward__sub_county__county': county
            }
        if sub_county:
            sub_county = SubCounty.objects.get(id=sub_county)
            queryset_filter = {
                'ward__sub_county': sub_county
            }
        if ward:
            ward = Ward.objects.get(id=ward)
            queryset_filter = {
                'ward': ward
            }

        for facility in Facility.objects.filter(
                **queryset_filter).filter(
            Q(number_of_beds__gt=0) | Q(number_of_cots__gt=0)):
            record = {
                'facility_id': str(facility.id),
                'facility_name': facility.name,
                'facility_code': facility.code,
                'number_of_beds': facility.number_of_beds,
                'number_of_cots': facility.number_of_cots
            }
            data.append(record)

        return data, []

    def _get_beds_and_cots(self, vals={}, filters={}):
        fields = vals.keys()
        assert len(fields) == 2
        items = Facility.objects.values(*fields).filter(**filters).annotate(
            cots=Sum('number_of_cots'), beds=Sum('number_of_beds')
        ).order_by()

        total_cots, total_beds = functools.reduce(
            lambda x, y: (x[0] + y['cots'], x[1] + y['beds']),
            items, (0, 0)
        )

        return [
            {
                'cots': p['cots'],
                'beds': p['beds'],
                vals[fields[0]]: p[fields[0]],
                vals[fields[1]]: p[fields[1]]
            } for p in items
        ], {'total_cots': total_cots, 'total_beds': total_beds}

        # Get the total number of facilities

    def _get_all_facility_details(self, vals={}, filters={}):

        fields = vals.keys()

        items = Facility.objects.values(
            'ward__sub_county__county__name',
            'ward__sub_county__county',
            'name',
            'facility_services',
            *fields
        ).filter(**filters).order_by()

        total_cots, total_beds = 0, 0

        # for item in items:
        #     total_cots += item['cots']
        #     total_beds += item['beds']

        return list(items), {'total_cots': total_cots, 'total_beds': total_beds}
        # items = Facility.objects.values(
        #        'name',
        #     # 'number_of_beds',
        #     # 'number_of_inpatient_beds',
        #     # 'number_of_cots',
        #     # 'number_of_emergency_casualty_beds',
        #     # 'number_of_icu_beds',
        #     # 'number_of_hdu_beds',
        #     # 'number_of_maternity_beds',
        #     # 'number_of_isolation_beds',
        #     # 'number_of_general_theatres',
        #     # 'number_of_maternity_theatres',
        #     'facility_services',
        #     # 'facility_infrastructure',
        #     'facility_contacts',
        #     # 'facility_humanresources',
        #     # 'owner',
        #     # 'facility_type',
        #     # 'keph_level',
        #     # 'regulatory_body')
        # ).distinct()
        # total_facilities=0

        # return list(items),{'total facilities',total_facilities}

    def _get_facility_report_all_hierachies(self, vals={}, filters={}):
        fields = vals.keys()

        keph_levels = KephLevel.objects.values_list('id', flat=True)

        items = Facility.objects.values(
            'ward__sub_county__name',
            'ward__sub_county__county__name',
            'ward__name',
            *fields
        ).filter(**filters).annotate(
            cots=Sum('number_of_cots'),
            beds=Sum('number_of_beds'),
            # Add other annotations for beds and cots here
        ).order_by()

        result = {}

        for item in items:
            ward_sub_county_name = item['ward__sub_county__name']
            ward_sub_county_county_name = item['ward__sub_county__county__name']
            ward_name = item['ward__name']

            keph_level_counts = {}

            for keph_level in keph_levels:
                keph_level_id = str(keph_level)
                count = item.get(keph_level_id, 0)
                keph_level_counts[keph_level_id] = count

            result_key = '{}_{}_{}'.format(ward_sub_county_name, ward_sub_county_county_name, ward_name)
            result[result_key] = {
                'ward__sub_county__name': ward_sub_county_name,
                'ward__sub_county__county__name': ward_sub_county_county_name,
                'ward__name': ward_name,
            }

            result[result_key].update(keph_level_counts)  # Update the dictionary

        return result

    # New report format (beds and cots)

    # new report beds and cots
    def _get_beds_and_cots_all_hierachies(self, vals={}, filters={}):
        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        page = self.request.query_params.get('page', 1)
        page_size = self.request.query_params.get('page_size', 10)
        paginate = self.request.query_params.get('paginate', True)
        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')
        if yearfilterby is not '':
            filters['date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility_type'] = filter_type
        if filter_owner is not '':
            filters['owner__owner_type'] = filter_owner

        if usertoplevel['usertoplevel'] == 'county':
            filters['ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['ward__sub_county__id'] = self.request.user.sub_countyid

        items = Facility.objects.values(
            'ward__sub_county__county__name',
            'ward__sub_county__county',
            'ward__sub_county__name',
            'ward__sub_county',
            'ward__name',
            'ward',
            'date_established',
            'keph_level',
            'keph_level__name',
            'facility_type',
            'facility_type__name',
            'owner',
            'owner__name',
            'owner__owner_type__name',
            *fields
        ).filter(**filters).annotate(
            cots=Sum('number_of_cots'),
            beds=Sum('number_of_beds'),
            maternity_beds=Sum('number_of_maternity_beds'),
            isolation_beds=Sum('number_of_isolation_beds'),
            hdu_beds=Sum('number_of_hdu_beds'),
            icu_beds=Sum('number_of_icu_beds'),
            emergency_casualty_beds=Sum('number_of_emergency_casualty_beds'),
            inpatient_beds=Sum('number_of_inpatient_beds'),
            general_theaters=Sum('number_of_general_theatres'),
            maternity_theaters=Sum('number_of_maternity_theatres'),
        ).order_by()

        county_totals = {}

        for item in items:
            group_byvalue = item['ward__sub_county__county__name']
            if groupby == 'county':
                group_byvalue = item['ward__sub_county__county__name']
            if groupby == 'sub_county':
                # page_size=50  implement paging later
                group_byvalue = item['ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['ward__name']

            if group_byvalue not in county_totals:
                county_totals[group_byvalue] = {
                    'general_totalbeds': int(item.get('cots',0) or 0)+int(item.get('beds',0) or 0)+int(item.get('maternity_beds',0) or 0)+int(item.get('isolation_beds',0) or 0)+
                                         int(item.get('hdu_beds', 0) or 0)+int(item.get('icu_beds',0) or 0)+int(item.get('emergency_casualty_beds',0) or 0)+int(item.get('inpatient_beds',0) or 0)+
                                         int(item.get('general_theaters', 0) or 0)+int(item.get('maternity_theaters',0) or 0),
                    'total_cots': int(item.get('cots',0) or 0),
                    'total_beds': int(item.get('beds',0) or 0),
                    'total_maternity_beds': int(item.get('maternity_beds',0) or 0),
                    'total_isolation_beds': int(item.get('isolation_beds',0) or 0),
                    'total_hdu_beds': int(item.get('hdu_beds',0) or 0),
                    'total_icu_beds': int(item.get('icu_beds',0) or 0),
                    'total_emergency_casualty_beds': int(item.get('emergency_casualty_beds',0) or 0),
                    'total_inpatient_beds': int(item.get('inpatient_beds',0) or 0),
                    'total_general_theaters': int(item.get('general_theaters',0) or 0),
                    'total_maternity_theaters': int(item.get('maternity_theaters',0) or 0),
                    'ward__sub_county__county__name' :item.get('ward__sub_county__county__name',''),
                    'ward__sub_county__name' :item.get('ward__sub_county__name',''),
                    'ward__name' :item.get('ward__name',''),
                    'date_established':item['date_established'],
                    'facility_keph_level':item['keph_level__name'],
                    'facility_owner':item['owner__owner_type__name'],
                    'facility_type_name':item['facility_type__name']
                }
            else:
                # Get total beds
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('cots',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('beds',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('maternity_beds',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('isolation_beds',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('hdu_beds',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('icu_beds',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('emergency_casualty_beds',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('inpatient_beds',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('general_theaters',0) or 0)
                county_totals[group_byvalue]['general_totalbeds'] += int(item.get('maternity_theaters',0) or 0)
               # add specific beds
                county_totals[group_byvalue]['total_cots'] += int(item.get('cots',0) or 0)
                county_totals[group_byvalue]['total_beds'] += int(item.get('beds',0) or 0)
                county_totals[group_byvalue]['total_maternity_beds'] += int(item.get('maternity_beds',0) or 0)
                county_totals[group_byvalue]['total_isolation_beds'] += int(item.get('isolation_beds',0) or 0)
                county_totals[group_byvalue]['total_hdu_beds'] += int(item.get('hdu_beds',0) or 0)
                county_totals[group_byvalue]['total_icu_beds'] += int(item.get('icu_beds',0) or 0)
                county_totals[group_byvalue]['total_emergency_casualty_beds'] += int(item.get('emergency_casualty_beds',0) or 0)
                county_totals[group_byvalue]['total_inpatient_beds'] += int(item.get('inpatient_beds',0) or 0)
                county_totals[group_byvalue]['total_general_theaters'] += int(item.get('general_theaters',0) or 0)
                county_totals[group_byvalue]['total_maternity_theaters'] += int(item.get('maternity_theaters',0) or 0)
                # Increment other properties accordingly

        total_cots, total_beds = 0, 0

        for item in items:
            total_cots += item['cots']
            total_beds += item['beds']

        return {'groupedby': groupby, 'results': county_totals}, {'total_cots': total_cots, 'total_beds': total_beds}

    def _get_facility_count_by_county(self):
        data = []
        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)

        obj_filter_param = {}
        area = None
        model = County
        facility_filter_str = 'ward__sub_county__county'

        if county:
            obj_filter_param = {
                'county_id__in': county.split(',')
            }
            model = SubCounty
            facility_filter_str = 'ward__sub_county'

        if sub_county:
            obj_filter_param = {
                'sub_county_id__in': sub_county.split(',')
            }
            model = Ward
            facility_filter_str = 'ward'

        for area in model.objects.filter(**obj_filter_param):
            facility_filter = {
                facility_filter_str: area
            }
            fac_count = Facility.objects.filter(
                **facility_filter).count()
            data_dict = {
                'area_name': area.name,
                'area_id': str(area.id),
                'number_of_facilities': fac_count
            }
            data.append(data_dict)

        return data, []

    def _get_facility_count_by_sub_county_in_county(self):
        data = []
        for county in County.objects.all():
            fac_count = Facility.objects.filter(
                ward__sub_county__county=county).count()
            data_dict = {
                'county_name': county.name,
                'county_id': str(county.id),
                'number_of_facilities': fac_count
            }
            data.append(data_dict)

        return data, []


    def _get_gis_report(self):

        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)
        page = self.request.query_params.get('page', 1)
        page_size = self.request.query_params.get('page_size', 10)
        paginate = self.request.query_params.get('paginate', True)
        allcounties = County.objects.all()
        allsubcounties = SubCounty.objects.all()
        allwards = Ward.objects.all()

        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        filters = {}
        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')
        if yearfilterby is not '':
            filters['facility__date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['facility__keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility__facility_type'] = filter_type
        if filter_owner is not '':
            filters['facility__owner__owner_type'] = filter_owner
        if usertoplevel['usertoplevel'] == 'county':
            filters['facility__ward__sub_county__county__id'] = self.request.user.countyid
            allcounties = County.objects.filter(id=self.request.user.countyid)
            allsubcounties = SubCounty.objects.filter(county__id=self.request.user.countyid)
            allwards = Ward.objects.filter(sub_county__county__id=self.request.user.countyid)
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['facility__ward__sub_county__id'] = self.request.user.sub_countyid
            allcounties = County.objects.filter(id=self.request.user.countyid)
            allsubcounties = SubCounty.objects.filter(id=self.request.user.sub_countyid)
            allwards = Ward.objects.filter(sub_county__id=self.request.user.sub_countyid)

        queryset = FacilityCoordinates.objects.filter(**filters).all()

        if county:
            queryset = queryset.filter(
                facility__ward__sub_county__county_id__in=county.split(','))
        if sub_county:
            queryset = queryset.filter(
                facility__ward__sub_county_id__in=sub_county.split('.'))
        if ward:
            queryset = queryset.filter(
                facility__ward_id__in=ward.split('.'))

        result_summary = {}
        results_total_count=0
        if groupby == 'county':
            paginator = Paginator(list(allcounties), page_size)
            results_total_count=len(allcounties)
            if paginate:
                allcounties = paginator.page(page)

            for group in allcounties:
                annotated_queryset = queryset.filter(facility__ward__sub_county__county__id=group.id).annotate(
                    facility_date_established=F('facility__date_established'),
                    facility_code=F('facility__code'),
                    facility_name=F('facility__name'),
                    facility_keph_level=F('facility__keph_level__name'),
                    facility_type_name=F('facility__facility_type__name'),
                    facility_owner=F('facility__owner__owner_type__name'),
                    facility_county=F('facility__ward__constituency__county__name'),
                    facility_ward=F('facility__ward__name'),
                    facility_lat=Func("coordinates", function="ST_Y", output_field=FloatField()),
                    facility_long=Func("coordinates", function="ST_X", output_field=FloatField()),
                    facility_sub_county=F('facility__ward__sub_county__name')
                ).values(
                    'facility_date_established',
                    'facility_code',
                    'facility_name',
                    'facility_keph_level',
                    'facility_type_name',
                    'facility_owner',
                    'facility_county',
                    'facility_ward',
                    'facility_lat',
                    'facility_long',
                    'facility_sub_county')

                result_summary[group.name] = list(annotated_queryset)
        if groupby == 'sub_county':
            page_size = self.request.query_params.get('page_size', 20)
            results_total_count = len(allsubcounties)
            paginator = Paginator(list(allsubcounties), page_size)
            if paginate:
                allsubcounties = paginator.page(page)
            for group in allsubcounties:
                annotated_queryset = queryset.filter(facility__ward__sub_county__id=group.id).annotate(
                    facility_date_established=F('facility__date_established'),
                    facility_code=F('facility__code'),
                    facility_name=F('facility__name'),
                    facility_keph_level=F('facility__keph_level__name'),
                    facility_type_name=F('facility__facility_type__name'),
                    facility_owner=F('facility__owner__owner_type__name'),
                    facility_county=F('facility__ward__constituency__county__name'),
                    facility_ward=F('facility__ward__name'),
                    facility_lat=Func("coordinates", function="ST_Y", output_field=FloatField()),
                    facility_long=Func("coordinates", function="ST_X", output_field=FloatField()),
                    facility_sub_county=F('facility__ward__sub_county__name')
                ).values(
                    'facility_date_established',
                    'facility_code',
                    'facility_name',
                    'facility_keph_level',
                    'facility_type_name',
                    'facility_owner',
                    'facility_county',
                    'facility_ward',
                    'facility_lat',
                    'facility_long',
                    'facility_sub_county')

                result_summary[group.name] = list(annotated_queryset)
        if groupby == 'ward':
            page_size = self.request.query_params.get('page_size', 150)
            results_total_count = len(allwards)
            paginator = Paginator(list(allwards), page_size)
            if paginate:
                allwards = paginator.page(page)
            for group in allwards:
                annotated_queryset = queryset.filter(facility__ward__id=group.id).annotate(
                    facility_date_established=F('facility__date_established'),
                    facility_code=F('facility__code'),
                    facility_name=F('facility__name'),
                    facility_keph_level=F('facility__keph_level__name'),
                    facility_type_name=F('facility__facility_type__name'),
                    facility_owner=F('facility__owner__owner_type__name'),
                    facility_county=F('facility__ward__constituency__county__name'),
                    facility_ward=F('facility__ward__name'),
                    facility_lat=Func("coordinates", function="ST_Y", output_field=FloatField()),
                    facility_long=Func("coordinates", function="ST_X", output_field=FloatField()),
                    facility_sub_county=F('facility__ward__sub_county__name')
                ).values(
                    'facility_date_established',
                    'facility_code',
                    'facility_name',
                    'facility_keph_level',
                    'facility_type_name',
                    'facility_owner',
                    'facility_county',
                    'facility_ward',
                    'facility_lat',
                    'facility_long',
                    'facility_sub_county')

                result_summary[group.name] = list(annotated_queryset)

        return {'groupedby': groupby, 'results': result_summary}, [results_total_count]

    # New report for nhif acredited facilities
    def _get_nhif_accreditation(self):

        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)
        page = self.request.query_params.get('page', 1)
        page_size = self.request.query_params.get('page_size', 10)
        paginate = self.request.query_params.get('paginate', True)
        allcounties = County.objects.all()
        allsubcounties = SubCounty.objects.all()
        allwards = Ward.objects.all()

        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        filters = {}
        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')
        filter_isnhifaccredited = self.request.query_params.get('filter_nhifaccredited', '')
        if yearfilterby is not '':
            filters['date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility_type'] = filter_type
        if filter_owner is not '':
            filters['owner__owner_type'] = filter_owner
        if filter_isnhifaccredited is not '':
            filters['nhif_accreditation'] = filter_isnhifaccredited
        else:
            filters['nhif_accreditation'] = True

        if usertoplevel['usertoplevel'] == 'county':
            filters['ward__sub_county__county__id'] = self.request.user.countyid
            allcounties = County.objects.filter(id=self.request.user.countyid)
            allsubcounties = SubCounty.objects.filter(county__id=self.request.user.countyid)
            allwards = Ward.objects.filter(sub_county__county__id=self.request.user.countyid)
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['ward__sub_county__id'] = self.request.user.sub_countyid
            allcounties = County.objects.filter(id=self.request.user.countyid)
            allsubcounties = SubCounty.objects.filter(id=self.request.user.sub_countyid)
            allwards = Ward.objects.filter(sub_county__id=self.request.user.sub_countyid)

        queryset = Facility.objects.filter(**filters).all()

        if county:
            queryset = queryset.filter(
                ward__sub_county__county_id__in=county.split(','))
        if sub_county:
            queryset = queryset.filter(
                ward__sub_county_id__in=sub_county.split('.'))
        if ward:
            queryset = queryset.filter(
                ward_id__in=ward.split('.'))

        result_summary = {}
        results_total_count=0
        if groupby == 'county':
            paginator = Paginator(list(allcounties), page_size)
            results_total_count=len(allcounties)
            if paginate:
                allcounties = paginator.page(page)

            for group in allcounties:
                annotated_queryset = queryset.filter(ward__sub_county__county__id=group.id).annotate(
                    facility_date_established=F('date_established'),
                    facility_code=F('code'),
                    facility_name=F('name'),
                    facility_keph_level=F('keph_level__name'),
                    facility_type_name=F('facility_type__name'),
                    facility_owner=F('owner__owner_type__name'),
                    facility_accredited=F('nhif_accreditation'),
                    facility_county=F('ward__constituency__county__name'),
                    facility_ward=F('ward__name'),
                    facility_sub_county=F('ward__sub_county__name')
                ).values(
                    'facility_date_established',
                    'facility_code',
                    'facility_name',
                    'facility_keph_level',
                    'facility_type_name',
                    'facility_owner',
                    'facility_accredited',
                    'facility_county',
                    'facility_ward',
                    'facility_sub_county')

                result_summary[group.name] = list(annotated_queryset)
        if groupby == 'sub_county':
            page_size = self.request.query_params.get('page_size', 20)
            results_total_count = len(allsubcounties)
            paginator = Paginator(list(allsubcounties), page_size)
            if paginate:
                allsubcounties = paginator.page(page)
            for group in allsubcounties:
                annotated_queryset = queryset.filter(ward__sub_county__id=group.id).annotate(
                    facility_date_established=F('date_established'),
                    facility_code=F('code'),
                    facility_name=F('name'),
                    facility_keph_level=F('keph_level__name'),
                    facility_type_name=F('facility_type__name'),
                    facility_owner=F('owner__owner_type__name'),
                    facility_accredited=F('nhif_accreditation'),
                    facility_county=F('ward__constituency__county__name'),
                    facility_ward=F('ward__name'),
                    facility_sub_county=F('ward__sub_county__name')
                ).values(
                    'facility_date_established',
                    'facility_code',
                    'facility_name',
                    'facility_keph_level',
                    'facility_type_name',
                    'facility_owner',
                    'facility_accredited',
                    'facility_county',
                    'facility_ward',
                    'facility_sub_county')

                result_summary[group.name] = list(annotated_queryset)
        if groupby == 'ward':
            page_size = self.request.query_params.get('page_size', 150)
            results_total_count = len(allwards)
            paginator = Paginator(list(allwards), page_size)
            if paginate:
                allwards = paginator.page(page)
            for group in allwards:
                annotated_queryset = queryset.filter(ward__id=group.id).annotate(
                    facility_date_established=F('facility__date_established'),
                    facility_code=F('code'),
                    facility_name=F('name'),
                    facility_keph_level=F('keph_level__name'),
                    facility_type_name=F('facility_type__name'),
                    facility_owner=F('owner__owner_type__name'),
                    facility_accredited=F('nhif_accreditation'),
                    facility_county=F('ward__constituency__county__name'),
                    facility_ward=F('ward__name'),
                    facility_sub_county=F('ward__sub_county__name')
                ).values(
                    'facility_date_established',
                    'facility_code',
                    'facility_name',
                    'facility_keph_level',
                    'facility_type_name',
                    'facility_owner',
                    'facility_accredited',
                    'facility_county',
                    'facility_ward',
                    'facility_sub_county')

                result_summary[group.name] = list(annotated_queryset)

        return {'groupedby': groupby, 'results': result_summary}, [results_total_count]

    # New report regulatory body
    def _get_facility_count_regulatory_body(self, vals={}, filters={}):
        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')
        if yearfilterby is not '':
            filters['date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility_type'] = filter_type
        if filter_owner is not '':
            filters['owner__owner_type'] = filter_owner

        if usertoplevel['usertoplevel'] == 'county':
            filters['ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['ward__sub_county__id'] = self.request.user.sub_countyid

        regulatory_body = RegulatingBody.objects.values('id', 'name')
        annotate_dict = {}  # Initialize the dictionary outside the loop

        annotate_dict = {
            reg['name']: Sum(Case(When(regulatory_body_id=reg['id'], then=1), output_field=IntegerField(), default=0))
            for reg in regulatory_body}

        items = Facility.objects.values(
            'ward__sub_county__county__name',
            'ward__sub_county__county',
            'date_established',
            'keph_level',
            'keph_level__name',
            'owner',
            'owner__name',
            'facility_type',
            'facility_type__name',
            'owner__owner_type__name',
            *fields
        ).filter(**filters).annotate(
            **annotate_dict
        ).order_by()
        result_summary = {}
        allcategories = RegulatingBody.objects.all()
        for item in items:
            if groupby == 'county':
                group_byvalue = item['ward__sub_county__county__name']
            if groupby == 'sub_county':
                group_byvalue = item['ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['ward__name']

            if group_byvalue not in result_summary:
                result_summary[group_byvalue] = {str(category.name).strip().replace(" ", '_'): item[str(category.name)] for category in
                                               allcategories}
                result_summary[group_byvalue]['date_established'] = item['date_established']
                result_summary[group_byvalue]['ward__sub_county__county__name'] = item['ward__sub_county__county__name']
                result_summary[group_byvalue]['ward__sub_county__name'] = item['ward__sub_county__name']
                result_summary[group_byvalue]['ward__name'] = item['ward__name']
                if filter_keph is not '':
                    result_summary[group_byvalue]['facility_keph_level'] = item['keph_level__name']
                else:
                    result_summary[group_byvalue]['facility_keph_level'] = 'All'
                if filter_type is not '':
                    result_summary[group_byvalue]['facility_type'] = item['facility_type__name']
                else:
                    result_summary[group_byvalue]['facility_type'] = 'All'
                if filter_owner is not '':
                    result_summary[group_byvalue]['facility_owner'] = item['owner__owner_type__name']
                else:
                    result_summary[group_byvalue]['facility_owner'] = 'All'
            else:
                for category in allcategories:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')] += item[str(category.name)]
        return {'groupedby': groupby, 'results': result_summary}, []

    #with annotaion of count
    def _get_facility_count_keph_level_oldannotation(self, vals=None, filters=None):
        if vals is None:
            vals = {}
        if filters is None:
            filters = {}

        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']

        # User custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')

        if yearfilterby:
            filters['date_established__year'] = yearfilterby
        if filter_keph:
            filters['keph_level'] = filter_keph
        if filter_type:
            filters['facility_type'] = filter_type
        if filter_owner:
            filters['owner__owner_type'] = filter_owner

        if usertoplevel['usertoplevel'] == 'county':
            filters['ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['ward__sub_county__id'] = self.request.user.sub_countyid

        all_kephs = KephLevel.objects.values('id', 'name')
        annotate_dict = {
            reg['name']: Sum(Case(When(keph_level_id=reg['id'], then=1), output_field=IntegerField(), default=0)) for
            reg in all_kephs
        }

        items = Facility.objects.values(
            'ward__sub_county__name',
            'ward__sub_county',
            'ward__name',
            'ward',
            'date_established',
            'keph_level',
            'keph_level__name',
            'owner',
            'owner__name',
            'facility_type',
            'facility_type__name',
            'owner__owner_type__name',
            *fields
        ).filter(**filters).annotate(
            **annotate_dict
        ).order_by()

        result_summary = {}
        allcategories = KephLevel.objects.all()
        for item in items:
            group_byvalue = None
            if groupby == 'county':
                group_byvalue = item.get('ward__sub_county__county__name')
            elif groupby == 'sub_county':
                group_byvalue = item.get('ward__sub_county__name')
            elif groupby == 'ward':
                group_byvalue = item.get('ward__name')

            if group_byvalue not in result_summary:
                result_summary[group_byvalue] = {
                    str(category.name).strip().replace(" ", '_'): item.get(category.name, 0) for category in
                    allcategories
                }
                result_summary[group_byvalue]['year_established'] = item['date_established']
                result_summary[group_byvalue]['ward__sub_county__county__name'] = item['ward__sub_county__county__name']
                result_summary[group_byvalue]['ward__sub_county__name'] = item['ward__sub_county__name']
                result_summary[group_byvalue]['ward__name'] = item['ward__name']
                result_summary[group_byvalue]['facility_keph_level'] = item[
                    'keph_level__name'] if filter_keph else 'All'
                result_summary[group_byvalue]['facility_type'] = item['facility_type__name'] if filter_type else 'All'
                result_summary[group_byvalue]['facility_owner'] = item[
                    'owner__owner_type__name'] if filter_owner else 'All'
            else:
                for category in allcategories:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')] += item.get(
                        category.name, 0)

        return {'groupedby': groupby, 'results': result_summary}, []

    def _get_facility_count_keph_level(self, vals=None, filters=None):
        if vals is None:
            vals = {}
        if filters is None:
            filters = {}

        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']

        # User custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')

        if yearfilterby:
            filters['date_established__year'] = yearfilterby
        if filter_keph:
            filters['keph_level'] = filter_keph
        if filter_type:
            filters['facility_type'] = filter_type
        if filter_owner:
            filters['owner__owner_type'] = filter_owner

        if usertoplevel['usertoplevel'] == 'county':
            filters['ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['ward__sub_county__id'] = self.request.user.sub_countyid

        regulatory_body = KephLevel.objects.values('id', 'name')
        keph_levels = {reg['id']: reg['name'] for reg in regulatory_body}

        facilities = Facility.objects.values(
            'ward__sub_county__name',
            'ward__sub_county__county__name',
            'ward__name',
            'date_established',
            'keph_level_id',
            'keph_level__name',
            'owner__owner_type__name',
            'facility_type__name',
            *fields
        ).filter(**filters)

        result_summary = {}
        allcategories = KephLevel.objects.all()
        for item in facilities:
            group_byvalue = None
            if groupby == 'county':
                group_byvalue = item.get('ward__sub_county__county__name')
            elif groupby == 'sub_county':
                group_byvalue = item.get('ward__sub_county__name')
            elif groupby == 'ward':
                group_byvalue = item.get('ward__name')

            if group_byvalue not in result_summary:
                result_summary[group_byvalue] = {
                    str(category.name).strip().replace(" ", '_'): 0 for category in allcategories
                }
                result_summary[group_byvalue]['year_established'] = item['date_established']
                result_summary[group_byvalue]['ward__sub_county__county__name'] = item['ward__sub_county__county__name']
                result_summary[group_byvalue]['ward__sub_county__name'] = item['ward__sub_county__name']
                result_summary[group_byvalue]['ward__name'] = item['ward__name']
                result_summary[group_byvalue]['facility_keph_level'] = item[
                    'keph_level__name'] if filter_keph else 'All'
                result_summary[group_byvalue]['facility_type'] = item['facility_type__name'] if filter_type else 'All'
                result_summary[group_byvalue]['facility_owner'] = item[
                    'owner__owner_type__name'] if filter_owner else 'All'

            for category in allcategories:
                if item['keph_level_id'] == category.id:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')] += 1

        return {'groupedby': groupby, 'results': result_summary}, []

    # new report facility owner
    def _get_facility_count_owner(self, vals={}, filters={}):
        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')
        if yearfilterby is not '':
            filters['date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility_type'] = filter_type
        if filter_owner is not '':
            filters['owner__owner_type'] = filter_owner

        if usertoplevel['usertoplevel'] == 'county':
            filters['ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['ward__sub_county__id'] = self.request.user.sub_countyid
        owners = Owner.objects.values('id', 'name')
        ownerTypes = OwnerType.objects.values('id', 'name')
        annotate_dict = {}  # Initialize the dictionary outside the loop
        annotate_dict2 = {}

        annotate_dict = {
            reg['name']: Sum(Case(When(owner_id=reg['id'], then=1), output_field=IntegerField(), default=0)) for reg in
            owners}
        annotate_dict2 = {
            reg['name']: Sum(Case(When(owner_id__owner_type=reg['id'], then=1), output_field=IntegerField(), default=0)) for reg in
            ownerTypes}

        items = Facility.objects.values(
            'ward__sub_county__county__name',
            'ward__sub_county__county',
            'date_established',
            'keph_level',
            'keph_level__name',
            'owner',
            'owner__name',
            'facility_type',
            'facility_type__name',
            'owner__owner_type__name',
            *fields
        ).filter(**filters).annotate(**annotate_dict)

        items = items.annotate(**annotate_dict2).order_by()

        result_summary = {}
        allcategories = OwnerType.objects.all()
        for item in items:
            if groupby == 'county':
                group_byvalue = item['ward__sub_county__county__name']
            if groupby == 'sub_county':
                group_byvalue = item['ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['ward__name']

            if group_byvalue not in result_summary:
                result_summary[group_byvalue]={}
                for category in allcategories:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')]=item.get(str(category.name),0)

                result_summary[group_byvalue]['date_established'] = item['date_established']
                result_summary[group_byvalue]['ward__sub_county__county__name'] = item['ward__sub_county__county__name']
                result_summary[group_byvalue]['ward__sub_county__name'] = item['ward__sub_county__name']
                result_summary[group_byvalue]['ward__name'] = item['ward__name']
                if filter_keph is not '':
                    result_summary[group_byvalue]['facility_keph_level'] = item['keph_level__name']
                else:
                    result_summary[group_byvalue]['facility_keph_level'] = 'All'
                if filter_type is not '':
                    result_summary[group_byvalue]['facility_type'] = item['facility_type__name']
                else:
                    result_summary[group_byvalue]['facility_type'] = 'All'
                if filter_owner is not '':
                    result_summary[group_byvalue]['facility_owner'] = item['owner__owner_type__name']
                else:
                    result_summary[group_byvalue]['facility_owner'] = 'All'
            else:
                for category in allcategories:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')] += item.get(category.name,0)
        return {'groupedby': groupby, 'results': result_summary}, []

    # New report facility type

    def _get_facility_count_facility_type(self, vals={}, filters={}):

        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')
        if yearfilterby is not '':
            filters['date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility_type'] = filter_type
        if filter_owner is not '':
            filters['owner__owner_type'] = filter_owner

        if usertoplevel['usertoplevel'] == 'county':
            filters['ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['ward__sub_county__id'] = self.request.user.sub_countyid
        facilitytype = FacilityType.objects.values('id', 'name')
        annotate_dict = {}  # Initialize the dictionary outside the loop

        annotate_dict = {
            reg['name']: Sum(Case(When(facility_type_id=reg['id'], then=1), output_field=IntegerField(), default=0)) for
            reg in facilitytype}
        annotate_dict2 = {
            reg['name']: Sum(Case(When(facility_type__parent_id=reg['id'], then=1), output_field=IntegerField(), default=0)) for
            reg in facilitytype}

        items = Facility.objects.values(
            'ward__sub_county__county__name',
            'ward__sub_county__county',
            'ward__name',
            'ward',
            'date_established',
            'keph_level',
            'keph_level__name',
            'owner',
            'owner__name',
            'facility_type',
            'facility_type__name',
            'owner__owner_type__name',
            *fields
        ).filter(**filters).annotate(
            **annotate_dict
        ).annotate(**annotate_dict2).order_by()

        result_summary = {}
        allcategories = FacilityType.objects.all().filter(parent_id=None)
        for item in items:
            if groupby == 'county':
                group_byvalue = item['ward__sub_county__county__name']
            if groupby == 'sub_county':
                group_byvalue = item['ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['ward__name']

            if group_byvalue not in result_summary:
                result_summary[group_byvalue]={}
                for category in allcategories:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')] = item.get(str(category.name), 0)

                result_summary[group_byvalue]['date_established'] = item['date_established']
                result_summary[group_byvalue]['ward__sub_county__county__name'] = item['ward__sub_county__county__name']
                result_summary[group_byvalue]['ward__sub_county__name'] = item['ward__sub_county__name']
                result_summary[group_byvalue]['ward__name'] = item['ward__name']
                if filter_keph is not '':
                    result_summary[group_byvalue]['facility_keph_level'] = item['keph_level__name']
                else:
                    result_summary[group_byvalue]['facility_keph_level'] = 'All'
                if filter_type is not '':
                    result_summary[group_byvalue]['facility_type'] = item['facility_type__name']
                else:
                    result_summary[group_byvalue]['facility_type'] = 'All'
                if filter_owner is not '':
                    result_summary[group_byvalue]['facility_owner'] = item['owner__owner_type__name']
                else:
                    result_summary[group_byvalue]['facility_owner'] = 'All'

            else:
                for category in allcategories:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')] += item.get(str(category.name), 0)

        return {'groupedby': groupby, 'results': result_summary}, []

        # New report faciity service

    def _get_facility_services(self, vals={}, filters={}):
        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']

        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')
        if yearfilterby is not '':
            filters['facility__date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['facility__keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility__facility_type'] = filter_type
        if filter_owner is not '':
            filters['facility__owner__owner_type'] = filter_owner

        if usertoplevel['usertoplevel'] == 'county':
            filters['facility__ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['facility__ward__sub_county__id'] = self.request.user.sub_countyid

        services = Service.objects.values('id', 'name', 'category_id', )
        servicescategory = ServiceCategory.objects.values('id','name')
        annotation = {}
        annotation2 = {}

        annotation = {reg['name']: Sum(Case(When(service_id=reg['id'], then=1), output_field=IntegerField(), default=0))
                      for reg in services}
        annotation2 = {reg['name']: Sum(
            Case(When(service_id__category=reg['id'], then=1), output_field=IntegerField(), default=0)) for reg
                       in servicescategory}

        items = FacilityService.objects.values(
            'facility__ward__sub_county__county__name',
            'facility__ward__sub_county__county',
            'facility__ward__sub_county__name',
            'facility__ward__sub_county',
            'facility__ward__name',
            'facility__ward',
            'facility__date_established',
            'facility__keph_level',
            'facility__keph_level__name',
            'facility__owner',
            'facility__owner__name',
            'facility__owner__owner_type__name',
            'facility__facility_type',
            'facility__facility_type__name',
        ).filter(**filters).annotate(**annotation)

        items = items.annotate(**annotation2).order_by()
        result_summary={}
        allcategories=ServiceCategory.objects.all()
        for item in items:
            if groupby == 'county':
                group_byvalue = item['facility__ward__sub_county__county__name']
            if groupby == 'sub_county':
                group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['facility__ward__name']

            if group_byvalue not in result_summary:
                result_summary[group_byvalue] = {}
                for category in allcategories:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')] = item.get(
                        str(category.name), 0)
                result_summary[group_byvalue]['facility__date_established']=item['facility__date_established']
                result_summary[group_byvalue]['ward__sub_county__county__name'] = item['facility__ward__sub_county__county__name']
                result_summary[group_byvalue]['ward__sub_county__name'] = item['facility__ward__sub_county__name']
                result_summary[group_byvalue]['ward__name'] = item['facility__ward__name']
                if filter_keph is not '':
                    result_summary[group_byvalue]['facility_keph_level'] = item['facility__keph_level__name']
                else:
                    result_summary[group_byvalue]['facility_keph_level'] = 'All'
                if filter_type is not '':
                    result_summary[group_byvalue]['facility_type'] = item['facility__facility_type__name']
                else:
                    result_summary[group_byvalue]['facility_type'] = 'All'
                if filter_owner is not '':
                    result_summary[group_byvalue]['facility_owner'] = item['facility__owner__owner_type__name']
                else:
                    result_summary[group_byvalue]['facility_owner'] = 'All'
            else:
                for category in allcategories:
                    result_summary[group_byvalue][str(category.name).strip().replace(" ", '_')] += item.get(str(category.name),0)
        return {'groupedby': groupby, 'results': result_summary}, []

        # New Facility report infrastructure

    def _get_facility_infrustructure(self, vals={}, filters={}):
        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')

        if yearfilterby is not '':
            filters['facility__date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['facility__keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility__facility_type'] = filter_type
        if filter_owner is not '':
            filters['facility__owner__owner_type'] = filter_owner

        if usertoplevel['usertoplevel'] == 'county':
            filters['facility__ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['facility__ward__sub_county__id'] = self.request.user.sub_countyid

        infrastructure = Infrastructure.objects.values('id', 'name', 'category_id', 'category_id__name')
        infrastructure_cat= InfrastructureCategory.objects.values('id','name')
        annotation = {}
        annotation2 = {}

        annotation = {
            reg['name']: Sum(Case(When(infrastructure_id=reg['id'], then=1), output_field=IntegerField(), default=0))
            for reg in infrastructure}
        annotation2 = {reg['name']: Sum(
            Case(When(infrastructure_id__category=reg['id'], then=1), output_field=IntegerField(), default=0))
                       for reg in infrastructure_cat}

        items = FacilityInfrastructure.objects.values(
            'facility__ward__sub_county__county__name',
            'facility__ward__sub_county__county',
            'facility__ward__sub_county__name',
            'facility__ward__sub_county',
            'facility__ward__name',
            'facility__ward',
            'facility__date_established',
            'facility__keph_level',
            'facility__keph_level__name',
            'facility__owner',
            'facility__owner__name',
            'facility__owner__owner_type__name',
            'facility__facility_type',
            'facility__facility_type__name',
        ).filter(**filters).annotate(**annotation)
        items = items.annotate(**annotation2).order_by()

        result_summary = {}
        result_summary_category = {}
        allcategories= InfrastructureCategory.objects.all()
        allinfrastructure = Infrastructure.objects.all()
        # get categories aggregation
        for item in items:
            group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'county':
                group_byvalue = item['facility__ward__sub_county__county__name']
            if groupby == 'sub_county':
                group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['facility__ward__name']
            if group_byvalue not in result_summary_category:
                result_summary_category[group_byvalue] = {}
                result_summary_category[group_byvalue]['facility__date_established']=item['facility__date_established']
                for category in allcategories:
                    result_summary_category[group_byvalue][str(category.name).strip().replace(" ",'_')]= item[str(category.name)]

                result_summary_category[group_byvalue]['ward__sub_county__county__name'] = item['facility__ward__sub_county__county__name']
                result_summary_category[group_byvalue]['ward__sub_county__name'] = item['facility__ward__sub_county__name']
                result_summary_category[group_byvalue]['ward__name'] = item['facility__ward__name']
                if filter_keph is not '':
                    result_summary_category[group_byvalue]['facility_keph_level'] = item['facility__keph_level__name']
                else:
                    result_summary_category[group_byvalue]['facility_keph_level'] = 'All'
                if filter_type is not '':
                    result_summary_category[group_byvalue]['facility_type'] = item['facility__facility_type__name']
                else:
                    result_summary_category[group_byvalue]['facility_type'] = 'All'
                if filter_owner is not '':
                    result_summary_category[group_byvalue]['facility_owner'] = item['facility__owner__owner_type__name']
                else:
                    result_summary_category[group_byvalue]['facility_owner'] = 'All'
            else:
                for category in allcategories:
                    result_summary_category[group_byvalue][str(category.name).strip().replace(" ",'_')] += item[str(category.name)]

        # get specific infrastructure aggregation
        for item in items:
            group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'county':
                group_byvalue = item['facility__ward__sub_county__county__name']
            if groupby == 'sub_county':
                group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['facility__ward__name']

            if group_byvalue not in result_summary:
                result_summary[group_byvalue] = {}
                result_summary[group_byvalue]['facility__date_established']=item['facility__date_established']
                if filter_keph is not '':
                    result_summary[group_byvalue]['facility_keph_level'] = item['facility__keph_level__name']
                else:
                    result_summary[group_byvalue]['facility_keph_level'] = 'All'
                if filter_type is not '':
                    result_summary[group_byvalue]['facility_type'] = item['facility__facility_type__name']
                else:
                    result_summary[group_byvalue]['facility_type'] = 'All'
                if filter_owner is not '':
                    result_summary[group_byvalue]['facility_owner'] = item['facility__owner__owner_type__name']
                else:
                    result_summary[group_byvalue]['facility_owner'] = 'All'
                for infra in allinfrastructure:
                    result_summary[group_byvalue][str(infra.name).strip().replace(" ", '_')] = item[str(infra.name)]

            else:
                for infra in allinfrastructure:
                    if str(infra.name).strip().replace(" ", '_') not in result_summary[group_byvalue]:
                        result_summary[group_byvalue][str(infra.name).strip().replace(" ", '_')] = item[str(infra.name)]
                    else:
                        result_summary[group_byvalue][str(infra.name).strip().replace(" ", '_')] += item[str(infra.name)]

        return {'groupedby': groupby, 'results_bycategory':result_summary_category, 'results': result_summary}, []

    def _get_facility_humanresource(self, vals={}, filters={}):
        fields = vals.keys()
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        if usertoplevel['usertoplevel'] == 'county':
            filters['facility__ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['facility__ward__sub_county__id'] = self.request.user.sub_countyid
        # user custom filters
        yearfilterby = self.request.query_params.get('report_year', '')
        filter_keph = self.request.query_params.get('filter_keph', '')
        filter_type = self.request.query_params.get('filter_type', '')
        filter_owner = self.request.query_params.get('filter_owner', '')

        if yearfilterby is not '':
            filters['facility__date_established__year'] = yearfilterby
        if filter_keph is not '':
            filters['facility__keph_level'] = filter_keph
        if filter_type is not '':
            filters['facility__facility_type'] = filter_type
        if filter_owner is not '':
            filters['facility__owner__owner_type'] = filter_owner

        speciality = Speciality.objects.values('id', 'name', 'category_id', 'category_id__name')
        annotation = {}
        annotation2 = {}

        annotation = {
            reg['name']: Sum(Case(When(speciality_id=reg['id'], then=1), output_field=IntegerField(), default=0))
            for reg in speciality}
        annotation2 = {reg['category_id__name']: Sum(
            Case(When(speciality_id__category=reg['category_id'], then=1), output_field=IntegerField(), default=0))
            for reg in speciality}

        items = FacilitySpecialist.objects.values(
            'facility__ward__sub_county__county__name',
            'facility__ward__sub_county__county',
            'facility__ward__sub_county__name',
            'facility__ward__sub_county',
            'facility__ward__name',
            'facility__ward',
            'facility__date_established',
            'facility__keph_level',
            'facility__keph_level__name',
            'facility__owner',
            'facility__owner__name',
            'facility__owner__owner_type__name',
            'facility__facility_type',
            'facility__facility_type__name',
        ).filter(**filters).annotate(**annotation)

        items = items.annotate(**annotation2).order_by()

        result_summary = {}
        result_summary_category = {}
        allcategories = SpecialityCategory.objects.all()
        allspecialities = Speciality.objects.all()

        for item in items:
            group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'county':
                group_byvalue = item['facility__ward__sub_county__county__name']
            if groupby == 'sub_county':
                group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['facility__ward__name']
            if group_byvalue not in result_summary_category:
                result_summary_category[group_byvalue] = {}
                result_summary_category[group_byvalue]['facility__date_established'] = item['facility__date_established']
                for category in allcategories:
                    result_summary_category[group_byvalue][str(category.name).strip().replace(" ",'_')] = item[str(category.name)]
                result_summary_category[group_byvalue]['ward__sub_county__county__name'] = item['facility__ward__sub_county__county__name']
                result_summary_category[group_byvalue]['ward__sub_county__name'] = item['facility__ward__sub_county__name']
                result_summary_category[group_byvalue]['ward__name'] = item['facility__ward__name']
                if filter_keph is not '':
                    result_summary_category[group_byvalue]['facility_keph_level'] = item['facility__keph_level__name']
                else:
                    result_summary_category[group_byvalue]['facility_keph_level'] = 'All'
                if filter_type is not '':
                    result_summary_category[group_byvalue]['facility_type'] = item['facility__facility_type__name']
                else:
                    result_summary_category[group_byvalue]['facility_type'] = 'All'
                if filter_owner is not '':
                    result_summary_category[group_byvalue]['facility_owner'] = item['facility__owner__owner_type__name']
                else:
                    result_summary_category[group_byvalue]['facility_owner'] = 'All'
            else:
                for category in allcategories:
                    result_summary_category[group_byvalue][str(category.name).strip().replace(" ",'_')] += item[str(category.name)]

        # get specific allspecialities aggregation
        for item in items:
                group_byvalue = item['facility__ward__sub_county__name']
                if groupby == 'county':
                    group_byvalue = item['facility__ward__sub_county__county__name']
                if groupby == 'sub_county':
                    group_byvalue = item['facility__ward__sub_county__name']
                if groupby == 'ward':
                    group_byvalue = item['facility__ward__name']
                if group_byvalue not in result_summary:
                    result_summary[group_byvalue] = {}
                    result_summary[group_byvalue]['facility__date_established']=item['facility__date_established']
                    if filter_keph is not '':
                        result_summary[group_byvalue]['facility_keph_level'] = item['facility__keph_level__name']
                    else:
                        result_summary[group_byvalue]['facility_keph_level'] = 'All'
                    if filter_type is not '':
                        result_summary[group_byvalue]['facility_type'] = item['facility__facility_type__name']
                    else:
                        result_summary[group_byvalue]['facility_type'] = 'All'
                    if filter_owner is not '':
                        result_summary[group_byvalue]['facility_owner'] = item['facility__owner__owner_type__name']
                    else:
                        result_summary[group_byvalue]['facility_owner'] = 'All'
                    for speciality in allspecialities:
                        result_summary[group_byvalue][str(speciality.name).strip().replace(" ", '_')] = item[str(speciality.name)]

                else:
                    for speciality in allspecialities:
                        if str(speciality.name).strip().replace(" ", '_') not in result_summary[group_byvalue]:
                            result_summary[group_byvalue][str(speciality.name).strip().replace(" ", '_')] = item[
                                str(speciality.name)]
                        else:
                            result_summary[group_byvalue][str(speciality.name).strip().replace(" ", '_')] += item[
                                str(speciality.name)]

        return {'groupedby': groupby, 'results_bycategory': result_summary_category,'results': result_summary}, []

    def _get_facility_count(self, category=True, f_type=False, keph=False):
        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)

        vals = []
        vals.append(county) if county else None
        vals.append(sub_county) if sub_county else None
        vals.append(ward) if ward else None

        for val in vals:
            try:
                for c in val.split(','):
                    uuid.UUID(c)
            except:
                raise ValidationError(
                    {
                        'Administrative area': [
                            'The area id provided is'
                            ' in the wrong format'
                        ]
                    }
                )

        owner_model = OwnerType if category else Owner
        if f_type:
            owner_model = FacilityType
        if keph:
            owner_model = KephLevel

        admin_area_filter = {}
        if county:
            admin_area_filter = {
                'ward__sub_county__county_id__in': county.split(',')
            }
        if sub_county:
            admin_area_filter = {
                'ward__sub_county_id__in': sub_county.split(',')
            }
        if ward:
            admin_area_filter = {
                'ward_id__in': ward.split(',')
            }
        data = []

        for owner in owner_model.objects.all():
            if category:
                owner_filter = {
                    'owner__owner_type': owner
                }
                field_name = 'owner_category'
            else:
                owner_filter = {
                    'owner': owner
                }
                field_name = 'owner'
            if f_type:
                owner_filter = {
                    'facility_type': owner
                }
                field_name = 'type_category'

            if keph:
                owner_filter = {
                    'keph_level': owner
                }
                field_name = 'keph_level'

            data_dict = {
                field_name: owner.name,
                'id': str(owner.id),
                'number_of_facilities': Facility.objects.filter(
                    **owner_filter).filter(
                    **admin_area_filter).count()
            }
            data.append(data_dict)
        return data, []

    def _get_facility_count_by_facility_type(self):
        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)

        vals = []
        vals.append(county) if county else None
        vals.append(sub_county) if sub_county else None
        vals.append(ward) if ward else None

        for val in vals:
            try:
                for c in val.split(','):
                    uuid.UUID(c)
            except:
                raise ValidationError(
                    {
                        'Administrative area': [
                            'The area id provided is'
                            ' in the wrong format'
                        ]
                    }
                )

        admin_area_filter = {}
        if county:
            admin_area_filter = {
                'ward__sub_county__county_id__in': county.split(',')
            }
        if sub_county:
            admin_area_filter = {
                'ward__sub_county_id__in': sub_county.split(',')
            }
        if ward:
            admin_area_filter = {
                'ward_id__in': ward.split(',')
            }
        data = []
        for ft in FacilityType.objects.filter(parent__isnull=True):
            ft_children = FacilityType.objects.filter(parent=ft)
            data_dict = {
                'type_category': ft.name,
                'id': str(ft.id),
                'number_of_facilities': Facility.objects.filter(
                    facility_type__in=ft_children).filter(
                    **admin_area_filter).count()
            }
            data.append(data_dict)
        return data, []

    def _get_facility_count_by_facility_type_details(self):
        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)
        parent = self.request.query_params.get('parent', None)

        vals = []
        vals.append(county) if county else None
        vals.append(sub_county) if sub_county else None
        vals.append(ward) if ward else None

        for val in vals:
            try:
                for c in val.split(','):
                    uuid.UUID(c)
            except:
                raise ValidationError(
                    {
                        'Administrative area': [
                            'The area id provided is'
                            ' in the wrong format'
                        ]
                    }
                )

        admin_area_filter = {}
        if county:
            admin_area_filter = {
                'ward__sub_county__county_id__in': county.split(',')
            }
        if sub_county:
            admin_area_filter = {
                'ward__sub_county_id__in': sub_county.split(',')
            }
        if ward:
            admin_area_filter = {
                'ward_id__in': ward.split(',')
            }
        data = []

        if parent:
            allowed_fts = FacilityType.objects.filter(parent_id=parent)
        else:
            allowed_fts = FacilityType.objects.filter(parent__isnull=False)

        wards = Ward.objects.filter(**admin_area_filter)

        for ward in wards:
            ward_data = {
                'ward__sub_county__name': ward.sub_county.county.name,
                'ward__sub_county__county__name': ward.sub_county.name,
                'ward__name': ward.name,
            }

            facility_counts = []

            for ft in allowed_fts:
                count = Facility.objects.filter(
                    facility_type=ft, ward=ward).count()
                facility_count = {
                    'type_category': ft.name,
                    'id': str(ft.id),
                    'number_of_facilities': count
                }
                facility_counts.append(facility_count)

            ward_data.update(facility_counts=facility_counts)
            data.append(ward_data)

        return data, []


class ReportView(FilterReportMixin, APIView):

    def get(self, *args, **kwargs):
        data, totals = self.get_report_data()

        return Response(data={
            'results': data,
            'total': totals
        })


class FacilityUpgradeDowngrade(APIView):

    def get(self, *args, **kwargs):
        county = self.request.query_params.get('county', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)
        see_facilities = self.request.query_params.get('see_facilities', None)
        upgrade = self.request.query_params.get('upgrade', None)

        right_now = timezone.now()
        last_week = self.request.query_params.get('last_week', None)
        last_month = self.request.query_params.get('last_month', None)
        last_three_months = self.request.query_params.get(
            'last_three_months', None)
        three_months_ago = right_now - timedelta(days=90)
        last_one_week = right_now - timedelta(days=7)
        last_one_month = right_now - timedelta(days=30)

        if upgrade in TRUTH_NESS:
            all_changes = FacilityUpgrade.objects.filter(
                is_upgrade=True)
        elif upgrade in FALSE_NESS:
            all_changes = FacilityUpgrade.objects.filter(
                is_upgrade=False)
        else:
            all_changes = FacilityUpgrade.objects.all()

        if last_week:
            all_changes = all_changes.filter(created__gte=last_one_week)
        if last_month:
            all_changes = all_changes.filter(created__gte=last_one_month)
        if last_three_months:
            all_changes = all_changes.filter(created__gte=three_months_ago)

        facilities_ids = [change.facility.id for change in all_changes]
        changed_facilities = Facility.objects.filter(id__in=facilities_ids)

        if not county and not sub_county:
            results = []
            for county in County.objects.all():
                facility_count = changed_facilities.filter(
                    ward__constituency__county=county).count()
                data = {
                    'area': county.name,
                    'area_id': county.id,
                    'changes': facility_count
                }
                results.append(data)
            return Response(data={
                'total_number_of_changes': len(facilities_ids),
                'results': results
            })
        if county and not sub_county:
            results = []
            for sub in SubCounty.objects.filter(county_id__in=county.split(',')):
                facility_count = changed_facilities.filter(
                    ward__sub_county=sub).count()
                data = {
                    'area': sub.name,
                    'area_id': sub.id,
                    'changes': facility_count
                }
                results.append(data)
            return Response(data={
                'total_number_of_changes': len(facilities_ids),
                'results': results
            })

        if county and sub_county:
            results = []
            sub_counties = sub_county.split(',')
            ward_filter = {
                'sub_county_id__in': sub_counties
            }
            if ward:
                wards = ward.split(',')
                ward_filter = {
                    'id__in': wards
                }
            for ward in Ward.objects.filter(**ward_filter):
                facility_count = changed_facilities.filter(
                    ward=ward).count()
                data = {
                    'area': ward.name,
                    'area_id': ward.id,
                    'changes': facility_count
                }
                results.append(data)
            return Response(data={
                'total_number_of_changes': len(facilities_ids),
                'results': results
            })

        if not county:
            facilities = changed_facilities.filter(ward__constituency__county_id=county)
            records = []
            for facility in facilities:
                latest_facility_change = FacilityUpgrade.objects.filter(facility=facility)[0]
                data = {
                    'name': facility.name,
                    'code': facility.code,
                    'current_keph_level':
                        latest_facility_change.keph_level.name,
                    'previous_keph_level':
                        latest_facility_change.current_keph_level_name,
                    'previous_facility_type':
                        latest_facility_change.current_facility_type_name,
                    'current_facility_type':
                        latest_facility_change.facility_type.name,
                    'reason': latest_facility_change.reason.reason
                }
                records.append(data)

            return Response(data={
                'total_facilities_changed': len(facilities),
                'results': records
            })

#for chus
class CommunityHealthUnitReport(APIView):
    queryset = CommunityHealthUnit.objects.all()

    def _get_user_top_level(self):
        userid = self.request.user.groups.all()[0].id
        groupby = self.request.query_params.get('report_groupby', '')
        resultobject = {'usertoplevel': '', 'userlowerlevels': [], 'usergroupby': 'sub_county'}
        resultobject['userlowerlevels'].append('ward')
        if userid == 5 or userid == 6 or userid == 7:
            resultobject['usertoplevel'] = 'national'
            resultobject['userlowerlevels'].append('national')
            if (groupby == 'county' or groupby == 'sub_county' or groupby == 'ward'):
                resultobject['usergroupby'] = groupby
            else:
                resultobject['usergroupby'] = 'county'
            return resultobject
        elif userid == 1 or userid == 12:
            resultobject['usertoplevel'] = 'county'
            resultobject['userlowerlevels'].append('county')
            if (groupby == 'county' or groupby == 'sub_county' or groupby == 'ward'):
                resultobject['usergroupby'] = groupby
            else:
                resultobject['usergroupby'] = 'county'
            return resultobject
        elif userid == 2:
            resultobject['usertoplevel'] = 'sub_county'
            resultobject['userlowerlevels'].append('sub_county')
            if (groupby == 'county' or groupby == 'sub_county' or groupby == 'ward'):
                resultobject['usergroupby'] = groupby
            else:
                resultobject['usergroupby'] = 'sub_county'
            return resultobject
        else:
            resultobject['usergroupby'] = groupby
            return resultobject

    def get_county_reports(self, queryset=queryset):
        data = []
        counties = County.objects.all()
        total_chus = 0
        for county in counties:
            chus = queryset.filter(
                facility__ward__constituency__county=county)
            chu_count = chus.count()
            total_chus += chu_count

            total_chvs = 0
            total_chews = 0

            for chu in chus:
                total_chews += chu.health_unit_workers.count()
                total_chvs += chu.number_of_chvs

            data.append(
                {
                    'county_name': county.name,
                    'county_id': county.id,
                    'number_of_units': chu_count,
                    'chvs': total_chvs,
                    'chews': total_chews
                }
            )
        return data, total_chus

    def get_constituency_reports(self, county=None, queryset=queryset):
        data = []
        constituencies = Constituency.objects.all()

        if county:
            constituencies = constituencies.filter(county_id=county)
        total_chus = 0
        for const in constituencies:
            chus = queryset.filter(
                facility__ward__constituency=const)
            chu_count = chus.count()
            total_chus += chu_count

            total_chvs = 0
            total_chews = 0
            for chu in chus:
                total_chews += chu.health_unit_workers.count()
                total_chvs += chu.number_of_chvs

            data.append(
                {
                    'constituency_name': const.name,
                    'constituency_id': const.id,
                    'number_of_units': chu_count,
                    'chvs': total_chvs,
                    'chews': total_chews
                }
            )
        return data, total_chus

    def get_sub_county_reports(self, county=None, queryset=queryset):
        data = []
        sub_county = SubCounty.objects.all()

        if county:
            sub_county = sub_county.filter(county_id=county)
        total_chus = 0
        for sub in sub_county:
            chus = queryset.filter(
                facility__ward__sub_county=sub)
            chu_count = chus.count()
            total_chus += chu_count

            total_chvs = 0
            total_chews = 0

            for chu in chus:
                total_chews += chu.health_unit_workers.count()
                total_chvs += chu.number_of_chvs

            data.append(
                {
                    'sub_county_name': sub.name,
                    'sub_county_id': sub.id,
                    'number_of_units': chu_count,
                    'chvs': total_chvs,
                    'chews': total_chews
                }
            )
        return data, total_chus

    def get_ward_reports(self, constituency=None, queryset=queryset):
        data = []
        wards = Ward.objects.all()
        if constituency:
            wards = wards.filter(sub_county_id=constituency)

        total_chus = 0
        for ward in wards:
            chus = queryset.filter(facility__ward=ward)
            chu_count = chus.count()
            total_chus += chu_count

            total_chvs = 0
            total_chews = 0

            for chu in chus:
                total_chews += chu.health_unit_workers.count()
                total_chvs += chu.number_of_chvs

            data.append(
                {
                    'ward_name': ward.name,
                    'ward_id': ward.id,
                    'number_of_units': chu_count,
                    'chvs': total_chvs,
                    'chews': total_chews,
                }
            )
        return data, total_chus

    def get_date_established_report(
            self, county=None, constituency=None):
        now = timezone.now()
        three_months_ago = now - timedelta(days=90)
        queryset = self.queryset.filter(created__gte=three_months_ago)

        if county:
            return self.get_constituency_reports(
                county=county, queryset=queryset)
        elif constituency:
            return self.get_ward_reports(
                constituency=constituency, queryset=queryset)
        else:
            return self.get_county_reports(queryset=queryset)

    def get_status_report(self, constituency=None, county=None, chu_list=False,
                          ward=None, sub_county=None):
        data = []
        if county:
            self.queryset = self.queryset.filter(
                facility__ward__constituency__county_id=county)

        if constituency:
            self.queryset = self.queryset.filter(
                facility__ward__constituency_id=constituency)

        if sub_county:
            self.queryset = self.queryset.filter(
                facility__ward__sub_county_id=sub_county)

        if ward:
            self.queryset = self.queryset.filter(
                facility__ward_id=ward)

        total_chus = 0
        status_filter = {}
        status_id = self.request.query_params.get('status', None)
        chu_list = self.request.query_params.get('chu_list', False)
        ward = self.request.query_params.get('ward', None)

        if ward:
            self.queryset = self.queryset.filter(
                facility__ward_id=ward)

        if status_id:
            status_filter = {
                'id__in': status_id.split(',')
            }
        if not chu_list:
            for status in Status.objects.filter(**status_filter):
                chu_count = self.queryset.filter(
                    status=status).count()
                total_chus += chu_count
                data.append(
                    {
                        'status_name': status.name,
                        'id': str(status.id),
                        'number_of_units': chu_count
                    }
                )
        else:
            if status_id:
                status_filter = {
                    'status_id__in': status_id.split(',')
                }
            for chu in self.queryset.filter(**status_filter):
                chu = {
                    'name': chu.name,
                    'id': str(chu.id),
                    'code': chu.code,
                    'facility_name': chu.facility.name,
                    'county': chu.facility.ward.constituency.county.name,
                    'sub_county': chu.facility.ward.constituency.name,
                    'ward': chu.facility.ward.name,
                    'date_established': chu.date_established.isoformat(),
                    'status': chu.status.name,
                    'number_of_chvs': chu.number_of_chvs
                }
                data.append(chu)
        return data, self.queryset.count()

    # new CHUL report functionality/status edited by felix
    def get_status_report_all_hierachies(self, filters={}):
        usertoplevel = self._get_user_top_level()
        groupby = self._get_user_top_level()['usergroupby']
        page = self.request.query_params.get('page', 1)
        total_items=0
        yearfilterby = self.request.query_params.get('report_year', '')
        chustatusfilterby = self.request.query_params.get('filter_chustatus', '')

        if yearfilterby is not '':
            filters['facility__date_established__year'] = yearfilterby
        if chustatusfilterby is not '':
            filters['status__name__iexact'] = chustatusfilterby
        if usertoplevel['usertoplevel'] == 'county':
            filters['facility__ward__sub_county__county__id'] = self.request.user.countyid
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['facility__ward__sub_county__id'] = self.request.user.sub_countyid
        parameterfilters = {}
        if self.request.query_params.get('ward'):
            parameterfilters['ward'] = self.request.query_params.get('ward')
        elif self.request.query_params.get('sub_county'):
            parameterfilters['sub_county'] = self.request.query_params.get('sub_county')
        elif self.request.query_params.get('county'):
            parameterfilters['county'] = self.request.query_params.get('county')

        allstatuses = Status.objects.all()

        annotate_dict = {
            reg.name: Sum(Case(When(status=reg.id, then=1), output_field=IntegerField(), default=0)) for reg in
            allstatuses}

        items = CommunityHealthUnit.objects.values(
            'facility__ward__sub_county__county__name',
            'facility__ward__sub_county__county',
            'facility__ward__sub_county__name',
            'facility__ward__sub_county',
            'facility__ward__name',
            'facility__ward',
            'facility__date_established'
        ).filter(**filters).annotate(**annotate_dict)
        result_summary = {}

        # get specific status aggregation

        for item in items:
            group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'county':
                group_byvalue = item['facility__ward__sub_county__county__name']
            if groupby == 'sub_county':
                group_byvalue = item['facility__ward__sub_county__name']
            if groupby == 'ward':
                group_byvalue = item['facility__ward__name']

            if group_byvalue not in result_summary:
                result_summary[group_byvalue] = {}
                result_summary[group_byvalue]['facility__date_established']=item['facility__date_established']
                result_summary[group_byvalue]['facility__ward']=item['facility__ward__name']
                result_summary[group_byvalue]['facility__subcounty']=item['facility__ward__sub_county__name']
                result_summary[group_byvalue]['facility__county']=item['facility__ward__sub_county__county__name']
                if chustatusfilterby is not '':
                    result_summary[group_byvalue]['chu_status'] = chustatusfilterby
                else:
                    result_summary[group_byvalue]['chu_status'] = 'all'
                for status in allstatuses:
                    result_summary[group_byvalue][str(status.name).strip().replace(" ", '_')] = item[str(status.name)]

            else:
                for status in allstatuses:
                    if str(status.name).strip().replace(" ", '_') not in result_summary[group_byvalue]:
                        result_summary[group_byvalue][str(status.name).strip().replace(" ", '_')] = item[str(status.name)]
                    else:
                        result_summary[group_byvalue][str(status.name).strip().replace(" ", '_')] += item[
                            str(status.name)]
        total_items=len(result_summary)
        return {'groupedby': groupby, 'results': result_summary}, total_items


    # new CHUL report services
    def get_services_report_all_hierachies(self, filters={}):
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']

        allwards = Ward.objects.all()
        allcounties = County.objects.all()
        allsubcounties = SubCounty.objects.all()
        page = self.request.query_params.get('page', 1)
        page_size = self.request.query_params.get('page_size', 50)
        paginate = self.request.query_params.get('paginate', True)
        current_page = page
        total_pages = 1
        total_items = 0
        yearfilterby = self.request.query_params.get('report_year', '')
        chustatusfilterby = self.request.query_params.get('filter_chustatus', '')
        if yearfilterby is not '':
            filters['health_unit__date_established__year'] = yearfilterby
        if chustatusfilterby is not '':
            filters['health_unit__status__name'] = chustatusfilterby
        if usertoplevel['usertoplevel'] == 'county':
            filters['health_unit__facility__ward__sub_county__county__id'] = self.request.user.countyid
            allcounties = allcounties.filter(id=self.request.user.countyid)
            allsubcounties = allsubcounties.filter(id=self.request.user.sub_countyid)
            allwards = allwards.filter(sub_county__county__id=self.request.user.countyid)
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['health_unit__facility__ward__sub_county__id'] = self.request.user.sub_countyid
            allcounties = allcounties.filter(id=self.request.user.countyid)
            allsubcounties = allsubcounties.filter(id=self.request.user.sub_countyid)
            allwards = allwards.filter(sub_county__id=self.request.user.sub_countyid)

        services = CHUService.objects.values('id', 'name')
        allchuservicelinks=CHUServiceLink.objects.filter(**filters)
        result_summary={}
        if groupby=='county':
            total_items=allcounties.count()
            for county in allcounties:
                result_summary[county.name] = {}
                result_summary[county.name]['health_unit__year_established'] = yearfilterby if yearfilterby else 'all'
                result_summary[county.name]['facility_county'] = county.name
                result_summary[county.name]['facility_subcounty'] = 'all'
                result_summary[county.name]['facility_ward'] = 'all'
                if chustatusfilterby is not '':
                    result_summary[county.name]['chu_status'] = chustatusfilterby
                else:
                    result_summary[county.name]['chu_status'] = 'all'
                for serv in services:
                    service_counts = allchuservicelinks.filter(service_id=serv['id'],
                                                                         health_unit__facility__ward__sub_county__county=county)
                    result_summary[county.name][serv['name']] = len(service_counts)

        if groupby == 'sub_county':
            total_items=allsubcounties.count()
            page_size=50
            total_pages=6
            paginator = Paginator(list(allsubcounties), page_size)
            allsubcounties=paginator.page(page)

            for subcounty in allsubcounties:
                result_summary[subcounty.name] = {}
                result_summary[subcounty.name]['health_unit__year_established'] = yearfilterby if yearfilterby else 'all'
                result_summary[subcounty.name]['facility_county'] = subcounty.county.name
                result_summary[subcounty.name]['facility_subcounty'] = subcounty.name
                result_summary[subcounty.name]['facility_ward'] = 'all'
                if chustatusfilterby is not '':
                    result_summary[subcounty.name]['chu_status'] = chustatusfilterby
                else:
                    result_summary[subcounty.name]['chu_status'] = 'all'
                for serv in services:
                    service_counts = allchuservicelinks.filter(service_id=serv['id'],
                                                                         health_unit__facility__ward__sub_county=subcounty)
                    result_summary[subcounty.name][serv['name']] = len(service_counts)
        if groupby == 'ward':
            total_items=allwards.count()
            page_size = 150
            total_pages=10
            paginator = Paginator(list(allwards), page_size)
            allwards = paginator.page(page)
            for ward in allwards:
                result_summary[ward.name] = {}
                result_summary[ward.name]['health_unit__year_established']=yearfilterby if yearfilterby else 'all'
                result_summary[ward.name]['facility_county'] = ward.sub_county.county.name
                result_summary[ward.name]['facility_subcounty'] = ward.sub_county.name
                result_summary[ward.name]['facility_ward'] = ward.name
                if chustatusfilterby is not '':
                    result_summary[ward.name]['chu_status'] = chustatusfilterby
                else:
                    result_summary[ward.name]['chu_status'] = 'all'
                for serv in services:
                    service_counts = allchuservicelinks.filter(service_id=serv['id'],
                                                                         health_unit__facility__ward=ward)
                    result_summary[ward.name][serv['name']] = len(service_counts)

        return {'groupedby':groupby, 'total_pages':total_pages,'current_page':current_page,'result_summary':result_summary}, total_items

        # new CHUL report  count chus

    def get_count_report_all_hierarchies_old(self, queryset=queryset):
        data = []
        wards = Ward.objects.all()

        total_chus = 0
        for ward in wards:
            chus = queryset.filter(facility__ward=ward)
            chu_count = chus.count()
            total_chus += chu_count

            total_chvs = 0
            total_chews = 0

            for chu in chus:
                total_chews += chu.health_unit_workers.count()
                total_chvs += chu.number_of_chvs

            data.append(
                {
                    'ward_name': ward.name,
                    'ward_id': ward.id,
                    'number_of_units': chu_count,
                    'chvs': total_chvs,
                    'chews': total_chews,
                    'county': ward.sub_county.county.name,
                    'sub county': ward.sub_county.name,

                }
            )
        return data, total_chus

    def get_count_report_all_hierarchies(self, queryset=queryset):
        usertoplevel = self._get_user_top_level()
        groupby = usertoplevel['usergroupby']
        toplevel_user = usertoplevel['usertoplevel']
        yearfilterby = self.request.query_params.get('report_year', '')
        chustatusfilterby = self.request.query_params.get('filter_chustatus', '')
        allwards = Ward.objects.all()
        allcounties = County.objects.all()
        allsubcounties = SubCounty.objects.all()
        filters={}
        if yearfilterby is not '':
            filters['facility__date_established__year'] = yearfilterby
        if chustatusfilterby is not '':
            filters['status__name'] = chustatusfilterby
        if usertoplevel['usertoplevel'] == 'county':
            filters['facility__ward__sub_county__county__id'] = self.request.user.countyid
            allcounties = allcounties.filter(id=self.request.user.countyid)
            allsubcounties = allsubcounties.filter(county__id=self.request.user.sub_countyid)
            allwards = allwards.filter(sub_county__county__id=self.request.user.countyid)
        if usertoplevel['usertoplevel'] == 'sub_county':
            filters['facility__ward__sub_county__id'] = self.request.user.sub_countyid
            allcounties = allcounties.filter(id=self.request.user.countyid)
            allsubcounties = allsubcounties.filter(id=self.request.user.sub_countyid)
            allwards = allwards.filter(sub_county__id=self.request.user.sub_countyid)
        newqueryset=queryset.filter(**filters)
        result_summary = {}
        total_chus = len(newqueryset)
        if groupby == 'county':
            for county in allcounties:
                groupby_value = county.name
                if groupby_value not in result_summary:
                    result_summary[groupby_value] = {}
                    result_summary[groupby_value]['number_of_units'] = len(
                        newqueryset.filter(facility__ward__sub_county__county__name=groupby_value))
                    total_chvs = sum(chu.number_of_chvs for chu in
                                     newqueryset.filter(facility__ward__sub_county__county__name=groupby_value))
                    result_summary[groupby_value]['chvs'] = total_chvs
                    total_chews = sum(chu.health_unit_workers.count() for chu in
                                      newqueryset.filter(facility__ward__sub_county__county__name=groupby_value))
                    result_summary[groupby_value]['chews'] = total_chews
                    result_summary[groupby_value]['facility_ward'] = 'all'
                    result_summary[groupby_value]['facility_subcounty'] = 'all'
                    result_summary[groupby_value]['facility_county'] = groupby_value
                    if chustatusfilterby is not '':
                        result_summary[groupby_value]['chu_status'] = chustatusfilterby
                    else:
                        result_summary[groupby_value]['chu_status'] = 'all'
                    if yearfilterby is not '':
                        result_summary[groupby_value]['date_establised'] = yearfilterby
                    else:
                        result_summary[groupby_value]['date_establised'] = 'all'
        if groupby== 'sub_county':
            for subcounty in allsubcounties:
                groupby_value = subcounty.name
                if groupby_value not in result_summary:
                    result_summary[groupby_value] = {}
                    result_summary[groupby_value]['number_of_units'] = len(
                        newqueryset.filter(facility__ward__sub_county__name=groupby_value))
                    total_chvs = sum(chu.number_of_chvs for chu in
                                     newqueryset.filter(facility__ward__sub_county__name=groupby_value))
                    result_summary[groupby_value]['chvs'] = total_chvs
                    total_chews = sum(chu.health_unit_workers.count() for chu in
                                      newqueryset.filter(facility__ward__sub_county__name=groupby_value))
                    result_summary[groupby_value]['chews'] = total_chews
                    result_summary[groupby_value]['facility_ward'] = 'all'
                    result_summary[groupby_value]['facility_subcounty'] = groupby_value
                    result_summary[groupby_value]['facility_county'] = subcounty.county.name
                    if chustatusfilterby is not '':
                        result_summary[groupby_value]['chu_status'] = chustatusfilterby
                    else:
                        result_summary[groupby_value]['chu_status'] = 'all'
                    if yearfilterby is not '':
                        result_summary[groupby_value]['date_establised'] = yearfilterby
                    else:
                        result_summary[groupby_value]['date_establised'] = 'all'
        if groupby == 'ward':
            for ward in allwards:
                groupby_value = ward.name
                if groupby_value not in result_summary:
                    result_summary[groupby_value] = {}
                    result_summary[groupby_value]['number_of_units'] = len(
                        newqueryset.filter(facility__ward__name=groupby_value))
                    total_chvs = sum(chu.number_of_chvs for chu in
                                     newqueryset.filter(facility__ward__name=groupby_value))
                    result_summary[groupby_value]['chvs'] = total_chvs
                    total_chews = sum(chu.health_unit_workers.count() for chu in
                                      newqueryset.filter(facility__ward__name=groupby_value))
                    result_summary[groupby_value]['chews'] = total_chews
                    result_summary[groupby_value]['facility_ward'] = groupby_value
                    result_summary[groupby_value]['facility_subcounty'] = ward.sub_county.name
                    result_summary[groupby_value]['facility_county'] = ward.sub_county.county.name
                    if chustatusfilterby is not '':
                        result_summary[groupby_value]['chu_status'] = chustatusfilterby
                    else:
                        result_summary[groupby_value]['chu_status'] = 'all'
                    if yearfilterby is not '':
                        result_summary[groupby_value]['date_establised'] = yearfilterby
                    else:
                        result_summary[groupby_value]['date_establised'] = 'all'

        return {'result_summary':result_summary,"groupedby":groupby}, total_chus

    def get(self, *args, **kwargs):
        county = self.request.query_params.get('county', None)
        constituency = self.request.query_params.get('constituency', None)
        sub_county = self.request.query_params.get('sub_county', None)
        ward = self.request.query_params.get('ward', None)
        report_type = self.request.query_params.get('report_type', None)
        last_quarter = self.request.query_params.get('last_quarter', None)
        chu_list = self.request.query_params.get('chu_list', False)

        # New report chul status ward level
        if report_type == 'chul_status_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id
            report_data = self.get_status_report_all_hierachies(filters=filters)

            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        # New report chul services ward level
        if report_type == 'chul_services_all_hierachies':
            county_id = self.request.query_params.get('county', None)
            constituency_id = self.request.query_params.get(
                'constituency', None
            )

            filters = {}

            if county_id is not None:
                filters['ward__sub_county__county__id'] = county_id
            if constituency_id is not None:
                filters['ward__sub_county__id'] = constituency_id
            report_data = self.get_services_report_all_hierachies(filters=filters)

            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

            # New report count chul at facility level
        if report_type == 'chul_count_all_hierachies':
            report_data = self.get_count_report_all_hierarchies()
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'constituency' and county:
            report_data = self.get_constituency_reports(county=county)

            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'sub_county':
            report_data = self.get_sub_county_reports(county=county)

            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'constituency' and not county:
            report_data = self.get_constituency_reports()
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'ward' and not constituency:
            report_data = self.get_ward_reports()
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'ward' and constituency:
            report_data = self.get_ward_reports(constituency=constituency)
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'ward' and chu_list:
            report_data = self.get_status_report()
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if last_quarter and county and not constituency:
            report_data = self.get_date_established_report(county=county)
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if last_quarter and constituency:
            report_data = self.get_date_established_report(
                constituency=constituency)
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if last_quarter and not county and not constituency:
            report_data = self.get_date_established_report()
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'status' and not county and not constituency:
            if not chu_list:
                report_data = self.get_status_report()
                data = {
                    'total': report_data[1],
                    'results': report_data[0]
                }
            else:
                report_data = self.get_status_report(chu_list=True)
                data = {
                    'total': report_data[1],
                    'results': report_data[0]
                }
            return Response(data)

        if report_type == 'status' and county and not constituency and not sub_county:
            report_data = self.get_status_report(county=county)
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'status' and not county and constituency:
            report_data = self.get_status_report(constituency=constituency)
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'status' and county and sub_county:
            report_data = self.get_status_report(sub_county=sub_county)
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        if report_type == 'status' and county and ward:
            report_data = self.get_status_report(ward=ward)
            data = {
                'total': report_data[1],
                'results': report_data[0]
            }
            return Response(data)

        data = {
            'total': self.get_county_reports()[1],
            'results': self.get_county_reports()[0]
        }
        return Response(data)
