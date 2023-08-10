from datetime import timedelta,datetime
from itertools import count 
import json

from django.utils import timezone
from django.db.models import Q

from rest_framework.views import APIView, Response
from common.models import County, SubCounty, Ward
from chul.models import CommunityHealthUnit
from users.models import MflUser

from ..models import (
    OwnerType,
    Owner,
    FacilityStatus,
    FacilityType,
    Facility,KephLevel
)
from ..views import QuerysetFilterMixin


class DashBoard(QuerysetFilterMixin, APIView):
    queryset = Facility.objects.all()
    
    def get_chu_count_in_county_summary(self, county):
        return CommunityHealthUnit.objects.filter(
            facility__ward__sub_county__county=county).count()

    def get_chu_count_in_constituency_summary(self, const):
        return CommunityHealthUnit.objects.filter(
            facility__ward__sub_county=const).count()

    def get_chu_count_in_ward_summary(self, ward):
        return CommunityHealthUnit.objects.filter(
            facility__ward=ward).count()

    def get_facility_county_summary(self,period_start,period_end):
        if not self.request.query_params.get('county'):
            counties = County.objects.all()
            if not self.request.user.is_national:
                counties = counties.filter(id=self.request.user.county.id)
                queryset = Facility.objects.filter(county=self.request.user.county)
        else:
            counties = [County.objects.get(id=self.request.query_params.get('county'))]
            queryset = self.get_queryset().filter(county=counties[0])
        facility_county_summary = {}
        for county in counties:
            facility_county_count = self.get_queryset().filter(ward__sub_county__county=county).count()
            facility_county_summary[str(county.name)] = facility_county_count
        top_10_counties = sorted(
            facility_county_summary.items(),
            key=lambda x: x[1], reverse=True)[0:94]
        facility_county_summary
        top_10_counties_summary = []
        for item in top_10_counties:
            county = County.objects.get(name=item[0])
            chu_count = self.get_chu_count_in_county_summary(county)
            top_10_counties_summary.append(
                {
                    "name": item[0],
                    "count": item[1],
                    "chu_count": chu_count
                })
        return top_10_counties_summary if self.request.user.is_national else []

    def get_facility_constituency_summary(self, period_start,period_end):
        if not self.request.query_params.get('sub_county'):
            constituencies =  SubCounty.objects.filter(
            county=self.request.user.county) \
            if not self.request.query_params.get('ward') and self.request.user.county  else []

        else:
            constituencies = [SubCounty.objects.get(id=self.request.query_params.get('sub_county'))]
     
        facility_constituency_summary = {}

        for const in constituencies:
            facility_const_count = self.get_queryset().filter(
                ward__sub_county=const).count()
            facility_constituency_summary[
                str(const.name)] = facility_const_count
        top_10_consts = sorted(
            facility_constituency_summary.items(),
            key=lambda x: x[1], reverse=True)[0:20]
        top_10_consts_summary = []
        for item in top_10_consts:
            const = SubCounty.objects.get(name=item[0])
            chu_count = self.get_chu_count_in_constituency_summary(const)
            top_10_consts_summary.append(
                
                {
                    "name": item[0],
                    "count": item[1],
                    "chu_count": chu_count
                })
        return top_10_consts_summary
        
    def get_facility_ward_summary(self,period_start,period_end):

        if not self.request.query_params.get('ward'):
            wards = Ward.objects.filter(
            sub_county=self.request.user.sub_county) \
            if self.request.user.sub_county else []

        else:
            wards = [Ward.objects.get(id=self.request.query_params.get('ward'))]
            
        
        facility_ward_summary = {}
        for ward in wards:
            facility_ward_count = self.get_queryset().filter(
                ward=ward).count()
            facility_ward_summary[
                str(ward.name + "|" + str(ward.code))] = facility_ward_count
        top_10_wards = sorted(
            facility_ward_summary.items(),
            key=lambda x: x[1], reverse=True)[0:20]
        top_10_wards_summary = []
        for item in top_10_wards:
            ward = Ward.objects.get(code=item[0].split('|')[1])
            chu_count = self.get_chu_count_in_ward_summary(ward)
            top_10_wards_summary.append(
                {
                    "name": item[0].split('|')[0],
                    "count": item[1],
                    "chu_count": chu_count
                })
        return top_10_wards_summary

    def get_facility_type_summary(self, cty, period_start,period_end):
        facility_type_parents_names = []
        for f_type in FacilityType.objects.all():
            if f_type.sub_division:
                facility_type_parents_names.append(f_type.sub_division)

        facility_types = FacilityType.objects.filter(
            sub_division__in=facility_type_parents_names)

        facility_type_summary = []
        summaries = {}
        for parent in facility_type_parents_names:
            summaries[parent] = 0

        for facility_type in facility_types:
            if self.request.query_params.get('ward'): 
                summaries[facility_type.sub_division] = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    facility_type=facility_type, ward=self.request.query_params.get('ward')).count()
            elif self.request.query_params.get('sub_county'):
                summaries[facility_type.sub_division] = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    facility_type=facility_type, sub_county=self.request.query_params.get('sub_county')).count()
            elif self.request.query_params.get('county'):
                 summaries[facility_type.sub_division] = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    facility_type=facility_type, county=self.request.query_params.get('county')).count()
            elif self.request.user.is_national:
                summaries[facility_type.sub_division] = summaries.get(
                        facility_type.sub_division) + self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                                facility_type=facility_type).count()
            else:
                if(self.mfluser.user_groups.get('is_sub_county_level')):
                    summaries[facility_type.sub_division] = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    facility_type=facility_type, sub_county=self.usersubcounty).count()
                elif(self.mfluser.user_groups.get('is_county_level')):
                    summaries[facility_type.sub_division] = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    facility_type=facility_type, county=self.usercounty).count()
                else:
                    summaries[facility_type.sub_division] =0
        
        facility_type_summary =  [
            {"name": key, "count": value } for key, value in summaries.items()
        ]

        facility_type_summary_sorted = sorted(
            facility_type_summary,
            key=lambda x: x, reverse=True)

        return facility_type_summary_sorted

    def get_facility_owner_summary(self, cty, period_start,period_end):
        owners = Owner.objects.all()

        facility_owners_summary = []
        for owner in owners:
            if self.request.query_params.get('ward'): 
                facility_owners_summary.append(
                    {
                        "name": owner.name,
                        "count": self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,
                            owner=owner, ward=self.request.query_params.get('ward')).count()
                    })
            elif self.request.query_params.get('sub_county'):
                 facility_owners_summary.append(
                        {
                            "name": owner.name,
                            "count": self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,
                                owner=owner, sub_county=self.request.query_params.get('sub_county')).count()
                        })
            elif self.request.query_params.get('county'):
                 facility_owners_summary.append(
                        {
                            "name": owner.name,
                            "count": self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,
                                owner=owner, county=self.request.query_params.get('county')).count()
                        })
            elif self.request.user.is_national:
                facility_owners_summary.append(
                    {
                        "name": owner.name,
                        "count": self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end, owner=owner).count()
                    })
            else:
                if(self.mfluser.user_groups.get('is_sub_county_level')):
                    facility_owners_summary.append(
                        {
                            "name": owner.name,
                            "count": self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,
                                owner=owner, sub_county=self.usersubcounty).count()
                        })
                elif(self.mfluser.user_groups.get('is_county_level')):
                    facility_owners_summary.append(
                        {
                            "name": owner.name,
                            "count": self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,
                                owner=owner, county=self.usercounty).count()
                        })
                else:
                    facility_owners_summary.append(
                        {
                            "name": owner.name,
                            "count": 0
                        })
                    
        return facility_owners_summary

    def get_facility_status_summary(self, cty, period_start,period_end):
        statuses = FacilityStatus.objects.all().filter(updated__gte=period_start, updated__lte=period_end)
        status_summary = []
        for status in statuses:
            if self.request.query_params.get('ward'):
                status_summary.append(
                        {
                            "name": status.name,
                            "count": self.get_queryset().filter( 
                                operation_status=status, ward=self.request.query_params.get('ward')).count()
                        })
            elif self.request.query_params.get('sub_county'):
                status_summary.append(
                        {
                            "name": status.name,
                            "count": self.get_queryset().filter(
                                operation_status=status, sub_county=self.request.query_params.get('sub_county')).count()
                        })
            elif self.request.query_params.get('county'):
                status_summary.append(
                        {
                            "name": status.name,
                            "count": self.get_queryset().filter( 
                                operation_status=status, county=self.usercounty).count()
                        })
            elif self.request.user.is_national:
                status_summary.append(
                    {
                        "name": status.name,
                        "count": self.get_queryset().filter(
                            operation_status=status).count()
                    })
            else:
                if(self.mfluser.user_groups.get('is_sub_county_level')):
                    status_summary.append(
                        {
                            "name": status.name,
                            "count": self.get_queryset().filter(
                                operation_status=status, sub_county=self.usersubcounty).count()
                        })
                elif(self.mfluser.user_groups.get('is_county_level')):
                    status_summary.append(
                        {
                            "name": status.name,
                            "count": self.get_queryset().filter( 
                                operation_status=status, county=self.usercounty).count()
                        })
                else:
                    status_summary.append(
                        {
                            "name": status.name,
                            "count": 0
                        })
                    

        return status_summary

    def get_facility_owner_types_summary(self, cty, period_start,period_end):
        owner_types = OwnerType.objects.all()
        owner_types_summary = []
        for owner_type in owner_types:
            if self.request.query_params.get('ward'): 
                 owner_types_summary.append(
                        {
                            "name": owner_type.name,
                            "count": self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                                owner__owner_type=owner_type, ward=self.request.query_params.get('ward')).count()
                        })
            elif self.request.query_params.get('sub_county'):
                owner_types_summary.append(
                        {
                            "name": owner_type.name,
                            "count": self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                                owner__owner_type=owner_type, sub_county=self.request.query_params.get('sub_county')).count()
                        })
            elif self.request.query_params.get('county'):
                owner_types_summary.append(
                        {
                            "name": owner_type.name,
                            "count": self.get_queryset().filter(
                                created__gte=period_start, created__lte=period_end,
                                owner__owner_type=owner_type, county=self.usercounty).count()
                        })
            elif self.request.user.is_national:
                owner_types_summary.append(
                    {
                        "name": owner_type.name,
                        "count": self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                            owner__owner_type=owner_type).count()
                    })
            else:
                if(self.mfluser.user_groups.get('is_sub_county_level')):
                    owner_types_summary.append(
                        {
                            "name": owner_type.name,
                            "count": self.get_queryset().filter(
                                created__gte=period_start, created__lte=period_end,
                                owner__owner_type=owner_type, sub_county=self.usersubcounty).count()
                        })
                elif(self.mfluser.user_groups.get('is_county_level')):
                    owner_types_summary.append(
                        {
                            "name": owner_type.name,
                            "count": self.get_queryset().filter(
                                created__gte=period_start, created__lte=period_end,
                                owner__owner_type=owner_type, county=self.usercounty).count()
                        })
                else:
                    owner_types_summary.append(
                        {
                            "name": owner_type.name,
                            "count": 0
                        })
        return owner_types_summary

    def get_recently_created_facilities(self, cty, period_start,period_end):
      
        if self.request.query_params.get('ward'): 
            return self.get_queryset().filter(created__gte=period_start, created__lte=period_end,ward=self.request.query_params.get('ward')).count()
        elif self.request.query_params.get('sub_county'):
            return self.get_queryset().filter(created__gte=period_start, created__lte=period_end,sub_county=self.request.query_params.get('sub_county')).count()
        elif self.request.query_params.get('county'):
            return self.get_queryset().filter(created__gte=period_start, created__lte=period_end,county=self.request.query_params.get('county')).count()
        elif self.request.user.is_national:
            return self.get_queryset().filter(created__gte=period_start, created__lte=period_end).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return self.get_queryset().filter(created__gte=period_start, created__lte=period_end,sub_county=self.usersubcounty).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return self.get_queryset().filter(created__gte=period_start, created__lte=period_end,county=self.usercounty).count()
            else:
                return 0
    
    def get_recently_updated_facilities(self, cty, period_start,period_end):
      
        if self.request.query_params.get('ward'): 
            return self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,ward=self.request.query_params.get('ward')).count()
        elif self.request.query_params.get('sub_county'):
            return self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,sub_county=self.request.query_params.get('sub_county')).count()
        elif self.request.query_params.get('county'):
            return self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,county=self.request.query_params.get('county')).count()
        elif self.request.user.is_national:
            return self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,sub_county=self.usersubcounty).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end,county=self.usercounty).count()
            else:
                return 0

    def get_recently_created_chus(self, cty, period_start,period_end):

        if self.request.query_params.get('ward'): 
                return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end,facility__ward=self.request.query_params.get('ward'),facility__in=self.get_queryset()).count()
        elif self.request.query_params.get('sub_county'):
                return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end,facility__ward__sub_county= self.request.query_params.get('sub_county'),facility__in=self.get_queryset()).count()
        elif self.request.query_params.get('county'):
                return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end,facility__ward__sub_county__county=self.request.query_params.get('county'),facility__in=self.get_queryset()).count()
        elif self.request.user.is_national:
            return self.get_queryset().filter(created__gte=period_start, created__lte=period_end).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end,facility__ward__sub_county=self.usersubcounty,facility__in=self.get_queryset()).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end,facility__ward__sub_county__county=self.usercounty,facility__in=self.get_queryset()).count()
            else:
                return 0
        
    def get_recently_updated_chus(self, cty, period_start,period_end):

        if self.request.query_params.get('ward'): 
                return CommunityHealthUnit.objects.filter(updated__gte=period_start, updated__lte=period_end,facility__ward=self.request.query_params.get('ward'),facility__in=self.get_queryset()).count()
        elif self.request.query_params.get('sub_county'):
                return CommunityHealthUnit.objects.filter(updated__gte=period_start, updated__lte=period_end,facility__ward__sub_county= self.request.query_params.get('sub_county'),facility__in=self.get_queryset()).count()
        elif self.request.query_params.get('county'):
                return CommunityHealthUnit.objects.filter(updated__gte=period_start, updated__lte=period_end,facility__ward__sub_county__county=self.request.query_params.get('county'),facility__in=self.get_queryset()).count()
        elif self.request.user.is_national:
            return self.get_queryset().filter(updated__gte=period_start, updated__lte=period_end).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return CommunityHealthUnit.objects.filter(updated__gte=period_start, updated__lte=period_end,facility__ward__sub_county=self.usersubcounty,facility__in=self.get_queryset()).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return CommunityHealthUnit.objects.filter(updated__gte=period_start, updated__lte=period_end,facility__ward__sub_county__county=self.usercounty,facility__in=self.get_queryset()).count()
            else:
                return 0
        
    def facilities_pending_approval_count(self, cty, period_start,period_end):
        if self.request.query_params.get('ward'): 
            updated_pending_approval = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    ward=self.request.query_params.get('ward'), has_edits=True)
            newly_created = self.queryset.filter(created__gte=period_start, created__lte=period_end,
                    ward=self.request.query_params.get('ward'), approved=False, rejected=False)
        elif self.request.query_params.get('sub_county'):
            updated_pending_approval = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    sub_county=self.request.query_params.get('sub_county'), has_edits=True)
            newly_created = self.queryset.filter(created__gte=period_start, created__lte=period_end,
                    sub_county=self.request.query_params.get('sub_county'), approved=False, rejected=False)
        elif self.request.query_params.get('county'):
            updated_pending_approval = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    county=self.request.query_params.get('county'), has_edits=True)
            newly_created = self.queryset.filter(created__gte=period_start, created__lte=period_end,
                    county=self.request.query_params.get('county'), approved=False, rejected=False)
        elif self.request.user.is_national:
            updated_pending_approval = self.get_queryset().filter(created__gte=period_start, created__lte=period_end, has_edits=True)
            newly_created = self.queryset.filter(created__gte=period_start, created__lte=period_end, approved=False, rejected=False)
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                updated_pending_approval = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    sub_county=self.usersubcounty, has_edits=True)
                newly_created = self.queryset.filter(created__gte=period_start, created__lte=period_end,
                    sub_county=self.usersubcounty, approved=False, rejected=False)
            elif(self.mfluser.user_groups.get('is_county_level')):
                updated_pending_approval = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,
                    sub_county=self.usercounty, has_edits=True)
                newly_created = self.queryset.filter(created__gte=period_start, created__lte=period_end,
                    sub_county=self.usercounty, approved=False, rejected=False)
            else:
                updated_pending_approval = self.get_queryset().filter(id__isnull=True)
                newly_created = self.get_queryset().filter(id__isnull=True)
         
        return len(
            list(set(list(updated_pending_approval) + list(newly_created)))
        )
   
    def get_facilities_approved_count(self,cty,period_start,period_end):

        if self.request.query_params.get('ward'): 
            return self.queryset.filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, approved=True, rejected=False, ward=self.request.query_params.get('ward')).count()
        elif self.request.query_params.get('sub_county'):
            return self.queryset.filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, approved=True, rejected=False, sub_county=self.request.query_params.get('sub_county')).count()
        elif self.request.query_params.get('county'):
            return self.queryset.filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, approved=True, rejected=False, county=self.request.query_params.get('county')).count()
        elif self.request.user.is_national:
            return self.queryset.filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, approved=True, rejected=False).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return self.queryset.filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, approved=True, rejected=False, sub_county=self.usersubcounty).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return self.queryset.filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, approved=True, rejected=False, county=self.usercounty).count()
            else:
                return 0
                

    def get_chus_pending_approval(self, cty,period_start,period_end):
        """
        Get the number of CHUs pending approval
        """
        if self.request.query_params.get('ward'): 
            return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end).filter(
                    Q(is_approved=False, is_rejected=False) |
                    Q(has_edits=True)).distinct().filter(
                        facility__in=self.get_queryset(),
                        facility__ward=self.request.query_params.get('ward')).count()
        elif self.request.query_params.get('sub_county'):
            return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end).filter(
                    Q(is_approved=False, is_rejected=False) |
                    Q(has_edits=True)).distinct().filter(
                        facility__in=self.get_queryset(), facility__sub_county=self.request.query_params.get('sub_county')).count()
        elif self.request.query_params.get('county'):
            return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end).filter(
                    Q(is_approved=False, is_rejected=False) |
                    Q(has_edits=True)).distinct().filter(
                        facility__in=self.get_queryset(), facility__county=self.usercounty).count()
        elif self.request.user.is_national:
            return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end).filter(
                Q(is_approved=False, is_rejected=False) |
                Q(has_edits=True)).distinct().filter(
                    facility__in=self.get_queryset()).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end).filter(
                    Q(is_approved=False, is_rejected=False) |
                    Q(has_edits=True)).distinct().filter(
                        facility__in=self.get_queryset(), facility__sub_county=self.usersubcounty).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return CommunityHealthUnit.objects.filter(created__gte=period_start, created__lte=period_end).filter(
                    Q(is_approved=False, is_rejected=False) |
                    Q(has_edits=True)).distinct().filter(
                        facility__in=self.get_queryset(), facility__county=self.usercounty).count()
            else:
                return 0

    def get_rejected_chus(self, cty,period_start,period_end):
        """
        Get the number of CHUs that have been rejected
        """
        if self.request.query_params.get('ward'): 
            return CommunityHealthUnit.objects.filter(
                    is_rejected=True, approval_date__gte=period_start, approval_date__lte=period_end,
                    facility__ward=self.request.query_params.get('ward')).count()
        elif self.request.query_params.get('sub_county'):
            return CommunityHealthUnit.objects.filter(
                    is_rejected=True,approval_date__gte=period_start, approval_date__lte=period_end,
                    facility__sub_county=self.request.query_params.get('sub_county')).count()
        elif self.request.query_params.get('county'):
            return CommunityHealthUnit.objects.filter(
                    is_rejected=True, approval_date__gte=period_start, approval_date__lte=period_end,
                    facility__county=self.request.query_params.get('county')).count()
        elif self.request.user.is_national:
            return CommunityHealthUnit.objects.filter(approval_date__gte=period_start, approval_date__lte=period_end, is_rejected=True).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return CommunityHealthUnit.objects.filter(
                    is_rejected=True,approval_date__gte=period_start, approval_date__lte=period_end,
                    facility__sub_county=self.usersubcounty).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return CommunityHealthUnit.objects.filter(
                    is_rejected=True,approval_date__gte=period_start, approval_date__lte=period_end,
                    facility__county=self.usercounty).count()
            else:
                return 0
  

    def get_rejected_facilities_count(self, cty, period_start,period_end):
        if self.request.query_params.get('ward'):
            return self.get_queryset().filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, rejected=True, ward=self.request.query_params.get('ward')).count()
        elif self.request.query_params.get('sub_county'):
            return self.get_queryset().filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, rejected=True, sub_county=self.request.query_params.get('sub_county')).count()
        elif self.request.query_params.get('county'):
            return self.get_queryset().filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, rejected=True, county=self.request.query_params.get('county')).count()
        elif self.request.user.is_national:
            return self.get_queryset().filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end,rejected=True).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return self.get_queryset().filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, rejected=True, sub_county=self.usersubcounty).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return self.get_queryset().filter(approvalrejection_date__gte=period_start, approvalrejection_date__lte=period_end, rejected=True, county=self.usercounty).count()
            else:
                return 0

    def get_closed_facilities_count(self, cty, period_start,period_end):
        if self.request.query_params.get('ward'):
            return self.get_queryset().filter(closed_date__gte=period_start, closed_date__lte=period_end,  ward=self.request.query_params.get('ward')).count()
        elif self.request.query_params.get('sub_county'):
            return self.get_queryset().filter(closed_date__gte=period_start, closed_date__lte=period_end,  sub_county=self.request.query_params.get('sub_county')).count()
        elif self.request.query_params.get('county'):
            return self.get_queryset().filter(closed_date__gte=period_start, closed_date__lte=period_end,  county=self.request.query_params.get('county')).count()
        elif self.request.user.is_national:
            return self.get_queryset().filter(closed_date__gte=period_start, closed_date__lte=period_end).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                return self.get_queryset().filter(closed_date__gte=period_start, closed_date__lte=period_end, sub_county=self.usersubcounty).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                return self.get_queryset().filter(closed_date__gte=period_start, closed_date__lte=period_end, county=self.usercounty).count()
            else:
                return 0
        
    def get_facilities_kephlevel_count(self,county_name,period_start,period_end):
        """
        Function to get facilities by keph level
        """  
        keph_level = KephLevel.objects.values("id", "name")  
        keph_array = []
        for keph in keph_level:
            if self.request.query_params.get('ward'): 
                keph_count = Facility.objects.filter(created__gte=period_start, created__lte=period_end, keph_level_id=keph.get("id"), ward=self.request.query_params.get('ward')).count()
                keph_array.append({"name" : keph.get("name"), "count" : keph_count})
            elif self.request.query_params.get('sub_county'):
                keph_count = Facility.objects.filter(created__gte=period_start, created__lte=period_end, keph_level_id=keph.get("id"), sub_county=self.request.query_params.get('sub_county')).count()
                keph_array.append({"name" : keph.get("name"), "count" : keph_count})
            elif self.request.query_params.get('county'):
                keph_count = Facility.objects.filter(created__gte=period_start, created__lte=period_end, keph_level_id=keph.get("id"), county=self.request.query_params.get('county')).count()
                keph_array.append({"name" : keph.get("name"), "count" : keph_count})
            elif self.request.user.is_national:
                keph_count = Facility.objects.filter(created__gte=period_start, created__lte=period_end, keph_level_id=keph.get("id")).count()
                keph_array.append({"name" : keph.get("name"), "count" : keph_count})
            else:
                if(self.mfluser.user_groups.get('is_sub_county_level')):
                    keph_count = Facility.objects.filter(created__gte=period_start, created__lte=period_end, keph_level_id=keph.get("id"), sub_county=self.usersubcounty).count()
                    keph_array.append({"name" : keph.get("name"), "count" : keph_count})
                elif(self.mfluser.user_groups.get('is_county_level')):
                    keph_count = Facility.objects.filter(created__gte=period_start, created__lte=period_end, keph_level_id=keph.get("id"), county=self.usercounty).count()
                    keph_array.append({"name" : keph.get("name"), "count" : keph_count})
                else:
                    keph_count = 0
                    keph_array.append({"name" : keph.get("name"), "count" : keph_count})
            

        return keph_array
        

        # if county_name:
        #     keph_level = KephLevel.objects.values("id", "name")  
        #     keph_array = []
        #     for keph in keph_level:
        #         keph_count = Facility.objects.filter(created__gte=period_start, created__lte=period_end, keph_level_id=keph.get("id"),ward__sub_county__county=county_name ).count()
        #         keph_array.append({"name" : keph.get("name"), "count" : keph_count})
        #     return keph_array

        # else:
        #     keph_level = KephLevel.objects.values("id", "name")  
        #     keph_array = []
        #     for keph in keph_level:
        #         keph_count = Facility.objects.filter(created__gte=period_start, created__lte=period_end, keph_level_id=keph.get("id")).count()
        #         keph_array.append({"name" : keph.get("name"), "count" : keph_count})

        #     return keph_array
       
    def get(self, *args, **kwargs):
        
        user = self.request.user 
        county_ = user.county  
        muser=MflUser.objects.filter(id=user.id)[0]
        self.mfluser=muser
        self.usercounty=muser.countyid
        self.usersubcounty=muser.sub_countyid
        period_start = self.request.query_params.get('datefrom')
        period_end = self.request.query_params.get('dateto') 
        if not period_end:
            period_end=datetime.max
        if not period_start:
            period_start=datetime.min 
        
    
        #get total facilities
        if self.request.query_params.get('ward'): 
            total_facilities = self.get_queryset().filter(created__gte=period_start, created__lte=period_end, ward=self.request.query_params.get('ward')).count()
        elif self.request.query_params.get('sub_county'):
            total_facilities = self.get_queryset().filter(created__gte=period_start, created__lte=period_end, sub_county=self.request.query_params.get('sub_county')).count()
        elif self.request.query_params.get('county'):
            total_facilities = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,county=self.request.query_params.get('county')).count() 
        elif self.request.user.is_national:
            total_facilities = self.queryset.filter(created__gte=period_start, created__lte=period_end).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                total_facilities = self.get_queryset().filter(created__gte=period_start, created__lte=period_end, sub_county=self.usersubcounty).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                total_facilities = self.get_queryset().filter(created__gte=period_start, created__lte=period_end,county=self.usercounty).count() 
            else:
                total_facilities=0
        
        #get total chus
        if self.request.query_params.get('ward'):
            total_chus = CommunityHealthUnit.objects.filter(date_established__gte=period_start, date_established__lte=period_end).filter(
                    facility__in=self.get_queryset().filter(ward=self.request.query_params.get('ward'))).count()
        elif self.request.query_params.get('sub_county'):
            total_chus = CommunityHealthUnit.objects.filter(date_established__gte=period_start, date_established__lte=period_end).filter(
                    facility__in=self.get_queryset().filter(sub_county=self.request.query_params.get('sub_county'))).count()
        elif self.request.query_params.get('county'):
            total_chus = CommunityHealthUnit.objects.filter(date_established__gte=period_start, date_established__lte=period_end).filter(
                    facility__in=self.get_queryset().filter(county=self.request.query_params.get('county'))).count()
        elif self.request.user.is_national:
            total_chus = CommunityHealthUnit.objects.filter(date_established__gte=period_start, date_established__lte=period_end).filter(facility__in=self.get_queryset()).count()
        else:
            if(self.mfluser.user_groups.get('is_sub_county_level')):
                total_chus = CommunityHealthUnit.objects.filter(date_established__gte=period_start, date_established__lte=period_end).filter(
                    facility__in=self.get_queryset().filter(sub_county=self.request.query_params.get('sub_county'))).count()
            elif(self.mfluser.user_groups.get('is_county_level')):
                total_chus = CommunityHealthUnit.objects.filter(date_established__gte=period_start, date_established__lte=period_end).filter(
                    facility__in=self.get_queryset().filter(county=self.request.query_params.get('county'))).count()
            else:
                total_chus=0
        

        #return data
        data = {
            "timeperiod":[{"startdate":period_start},{"enddate":period_end}],
            "keph_level" : self.get_facilities_kephlevel_count(county_,period_start,period_end),
            "total_facilities": total_facilities,
            "county_summary": self.get_facility_county_summary(period_start,period_end)
            if user.is_national else [],
            "constituencies_summary": self.get_facility_constituency_summary(period_start,period_end),
            # if user.county and not user.sub_county else [],
            "wards_summary": self.get_facility_ward_summary(period_start,period_end),
            # if user.sub_county else [],
            "owners_summary": self.get_facility_owner_summary(county_,period_start,period_end),
            "types_summary": self.get_facility_type_summary(county_,period_start,period_end),
            "status_summary": self.get_facility_status_summary(county_,period_start,period_end),
            "owner_types": self.get_facility_owner_types_summary(county_,period_start,period_end),
            "recently_created": self.get_recently_created_facilities(county_,period_start,period_end),
            "recently_updated": self.get_recently_updated_facilities(county_,period_start,period_end),
            "recently_created_chus": self.get_recently_created_chus(county_,period_start,period_end),
            "recently_updated_chus": self.get_recently_updated_chus(county_,period_start,period_end),
            "pending_updates": self.facilities_pending_approval_count(county_,period_start,period_end),
            "rejected_facilities_count": self.get_rejected_facilities_count(county_,period_start,period_end),
            "closed_facilities_count": self.get_closed_facilities_count(county_,period_start,period_end),
            "rejected_chus": self.get_rejected_chus(county_,period_start,period_end),
            "chus_pending_approval": self.get_chus_pending_approval(county_,period_start,period_end),
            "total_chus": total_chus,
            "approved_facilities": self.get_facilities_approved_count(county_,period_start,period_end),

        }

        fields = self.request.query_params.get("fields", None)
       
        if fields:
            required = fields.split(",")
            required_data = {
                i: data[i] for i in data if i in required
            }
            return Response(required_data)
        return Response(data)

#facility_county_summary
# if self.request.query_params.get('ward'): 
# elif self.request.query_params.get('sub_county'):
# elif self.request.query_params.get('county'):
# elif self.request.user.is_national:
# else:
#     if(self.mfluser.user_groups.get('is_sub_county_level')):
#     elif(self.mfluser.user_groups.get('is_county_level')):
#     else:

#keph level, recently_created_chus,recently_created