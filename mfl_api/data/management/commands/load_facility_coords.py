import json
import os
from common.renderers.excel_renderer import _write_excel_file

import logging
from django.contrib.gis.geos import Point
from users.models import MflUser
from django.core.management import BaseCommand
from django.conf import settings
from facilities.models import Facility


from mfl_gis.models import WardBoundary

system_user = MflUser.objects.get(email='system@ehealth.or.ke')


logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        facility_file = 'data/new_data/demo/0016_facilities.json'
        file_path = os.path.join(
            settings.BASE_DIR, facility_file)
        facility_codes_with_errors = []
        missed_codes_file_path = os.path.join(settings.BASE_DIR,
            'data/management/commands/missed_facility_codes.txt')

        with open(missed_codes_file_path) as missed_codes_file:
            the_codes = missed_codes_file.read()
            facility_codes_with_errors = the_codes.split('\n')


        with open(file_path) as facility_data:
            data = json.load(facility_data)
            records = data[0].get('records')
            new_records = []
            new_error_records = []
            errors = []
            index = 0
            for record in records:
                if str(record.get('code')) in facility_codes_with_errors:
                    try:
                        Facility.objects.get(code=int(record.get('code')))
                    except Facility.DoesNotExist:
                        new_error_records.append(record)
                    continue
                else:
                    continue

                error_rec = {
                    'facility_code': record.get('code'),
                    'facility_name': record.get('name'),
                    'county': record.pop('county'),
                    'division': record.pop('division', None),
                    'reasons': [],
                }
                try:
                    Facility.objects.get(code=record.get('code'))
                    continue
                except Facility.DoesNotExist:
                    index = index + 1
                    print index, record.get('code')

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
                new_records.append(record)
                print record.get('name'), ward.name,

        with open('missed_live_codes_facility_records.json', 'w+') as missed_fac_file:

            json.dump(new_error_records, missed_fac_file, indent=4)
            print len(new_error_records)

        # # overwrite the facilities file
        # with open(file_path, 'w') as fac_file:
        #     fac_data = [
        #         {
        #             "model": "facilities.Facility",
        #             "unique_fields": [
        #                 "code"
        #             ],
        #             "records": new_records
        #         }
        #     ]
        #     json.dump(fac_data, fac_file, indent=4)


        # # write the erors file
        # with open('new_facs_errors.json', 'w+') as fac_error_file:
        #     json.dump(errors, fac_error_file, indent=4)
        #     try:
        #         excel_file = open('errors_file.xlsx', 'wb+')
        #         excel_file.write(_write_excel_file(errors))
        #         excel_file.close()
        #     except:
        #         pass
        # #
