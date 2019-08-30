import json
import os
from common.renderers.excel_renderer import _write_excel_file

import logging
from django.contrib.gis.geos import Point
from users.models import MflUser
from django.core.management import BaseCommand
from django.conf import settings


from mfl_gis.models import FacilityCoordinates, GeoCodeMethod, GeoCodeSource
from facilities.models import Facility


system_user = MflUser.objects.get(email='system@ehealth.or.ke')


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        facility_file = 'data/new_data/geocodes/live_facility_codes.json'
        file_path = os.path.join(
            settings.BASE_DIR, facility_file)
        with open(file_path) as facility_data:
            data = json.load(facility_data)
            for record in data[0].get('records'):
                latitude = record.get('latitude')
                longitude = record.get('longitude')
                if latitude and longitude:
                    try:

                        point = Point(x=float(longitude), y=float(latitude))
                    except ValueError:
                        print "Badly formated coordinates"
                        continue
                    try:
                        facility = Facility.objects.get(code=record.get('facility').get('code'))
                    except Facility.DoesNotExist:
                        print "The requested facility does not exist"
                        continue


                    fc = FacilityCoordinates(
                        facility=facility, coordinates=point,
                        created_by=system_user, updated_by=system_user
                    )
                    try:
                        fc.save()
                    except:
                        print "coordinates ni mbaya"
                else:
                    print "There is a missing coordinate"
