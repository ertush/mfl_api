from datetime import timedelta
from itertools import count

from django.utils import timezone
from django.db.models import Q

from rest_framework.views import APIView, Response
from common.models import County, SubCounty, Ward
from chul.models import CommunityHealthUnit

from ..models import (
    OwnerType,
    Owner,
    FacilityStatus,
    FacilityType,
    Facility,KephLevel
)
from ..views import QuerysetFilterMixin


class StaticReport(QuerysetFilterMixin, APIView):
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

    def get_bed_count(self, location):
        import pdb
        if location:

            pdb.set_trace()
            # for keph in keph_level:
                # objects.values('Category').distinct()
            facility_beds_details = Facility.objects.values("number_of_cots", "number_of_beds","number_of_hdu_beds", "number_of_icu_beds", "number_of_isolation_beds","number_of_maternity_beds","owner_id","county_id", "facility_type_id","keph_level_id", "sub_county_id","ward_id", ward__sub_county__county=location)  

            return "keph_array"
        else:
            # pdb.set_trace()
            counties = County.objects.values("id","name","code")
            facility_beds_details = Facility.objects.values("number_of_cots", "number_of_beds","number_of_hdu_beds", "number_of_icu_beds", "number_of_isolation_beds","number_of_maternity_beds","owner_id","county_id", "facility_type_id","keph_level_id", "sub_county_id","ward_id")  
            counties_beds_array = []

            cobedunter = 0
            for county in counties:
                for beds_details in facility_beds_details:
                    if beds_details.get("county_id") is not None and beds_details.get("county_id")==county.get("id"):
                        counties_beds_array.append({
                            "county_name" : county.get("name"),
                            "count" : beds_details.get("number_of_beds")
                        })
            summary=[]            
            final_sum = {}
            
            for county_data in counties_beds_array:   
                # print("---------", county_data.get("county_name") != final_sum.get("county"))
                if county_data.get("county_name") != final_sum.get("county"):
                    final_sum[county_data.get("county_name")] = county_data.get("count")
                elif county_data.get("county_name") == final_sum.get("county"):
                    final_sum[county_data.get("county_name")] = county_data.get("count")+county_data.get("count")

            summary =  [
            {"name": key, "count": value } for key, value in final_sum.items()
            ]        
            return summary

    

    def get(self, *args, **kwargs):
        user = self.request.user
        county_ = user.county
        if not self.request.query_params.get('county'):
            county_ = user.county
        else:
            county_ = County.objects.get(id=self.request.query_params.get('county'))

        data = {
            "beds_by_county" : self.get_bed_count(county_),

        }

        fields = self.request.query_params.get("fields", None)
        if fields:
            required = fields.split(",")
            required_data = {
                i: data[i] for i in data if i in required
            }
            return Response(required_data)
        return Response(data)
