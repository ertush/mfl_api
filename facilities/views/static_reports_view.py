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
            my_array = []

            counter = 0
            for beds_details in facility_beds_details:
                for county in counties:
                    # print(type(county.get("id")))
                    if beds_details.get("county_id") is not None and beds_details.get("county_id")==county.get("id"):
                        my_array.append({
                            "county_name" : county.get("name"),
                            "count" : beds_details.get("number_of_beds")
                        })
            print("wwwwwwwwwwwwwwwwwwwww")


                
            return "keph_array"

    

    def get(self, *args, **kwargs):
        import pdb
        user = self.request.user
        county_ = user.county
        if not self.request.query_params.get('county'):
            county_ = user.county
        else:
            county_ = County.objects.get(id=self.request.query_params.get('county'))
        # pdb.set_trace()
        print("*************** ",county_)
        
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
