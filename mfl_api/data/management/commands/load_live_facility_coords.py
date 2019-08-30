import json
import os
from common.renderers.excel_renderer import _write_excel_file

import logging
from django.contrib.gis.geos import Point
from users.models import MflUser
from django.core.management import BaseCommand
from django.conf import settings


from mfl_gis.models import WardBoundary

system_user = MflUser.objects.get(email='system@ehealth.or.ke')


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        facility_file = 'data/new_data/demo/0017_facilities.json'
        file_path = os.path.join(
            settings.BASE_DIR, facility_file)
        with open(file_path) as facility_data:
            data = json.load(facility_data)
            records = data[0].get('records')
            new_records = []
            errors = []
            for record in records:

                error_rec = {
                    'facility_code': record.get('code'),
                    'facility_name': record.get('name'),
                    'reasons': [],
                }
                if not record:
                    errors.append(error_rec)
                    continue

                latitude = record.pop('latitude', None)
                longitude = record.pop('longitude', None)
                if not latitude:
                    print "latitude missing"
                    error_rec['reasons'].append('Latitude is missing')

                if not longitude:
                    print "longitude missing"
                    error_rec['reasons'].append('Longitude is missing')

                if not latitude or not longitude:
                    errors.append(error_rec)
                    continue
                try:

                    point = Point(x=float(longitude), y=float(latitude))
                except ValueError:
                    error_rec['reasons'].append("Wrongly formatted geocodes")
                    errors.append(error_rec)
                    continue

                try:
                    possible_wards = WardBoundary.objects.filter(
                        mpoly__contains=point)
                    ward = possible_wards[0].area
                except IndexError:
                    print "bad lat long"
                    error_rec['reasons'].append('Erroneous coordinates ')
                    errors.append(error_rec)
                    continue


                record['ward'] = {
                    'id': str(ward.id)
                }
                # ensure all records are in
                fields = [
                     "code",
                    "name",
                    "official_name",
                    "created",
                    "regulatory_body",
                    "facility_type",
                    "owner",
                    "operation_status",
                    "ward",
                ]
                has_missing_fields = False
                for field in fields:

                    if field not in record.keys():

                        error_rec['reasons'].append('field {} is missing'.format(field))
                        has_missing_fields = True

                if has_missing_fields:
                    continue

                new_records.append(record)
                print record.get('name'), ward.name,

        # overwrite the facilities file
        with open(file_path, 'w') as fac_file:
            fac_data = [
                {
                    "model": "facilities.Facility",
                    "unique_fields": [
                        "code"
                    ],
                    "records": new_records
                }
            ]
            json.dump(fac_data, fac_file, indent=4)

        # write the errors file
        with open('new_live_facs_errors.json', 'w+') as fac_error_file:
            json.dump(errors, fac_error_file, indent=4)
            try:
                excel_file = open('live_facilities_errors_file.xlsx', 'wb+')
                excel_file.write(_write_excel_file(errors))
                excel_file.close()
            except:
                pass
        #
