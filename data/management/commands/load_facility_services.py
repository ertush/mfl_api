import os
import json

from django.core.management import BaseCommand
from django.conf import settings

from facilities.models import Facility, FacilityService, Service
from users.models import MflUser
system_user = MflUser.objects.get(email='system@ehealth.or.ke')

from common.renderers.excel_renderer import _write_excel_file


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/setup/00012_services.json'
        )
        errors = []
        with open(file_path) as data_file:
            data = json.load(data_file)
            records = data[0].get('records')

            for record in records:

                facility_code = record.get('code')
                service_name = record.get('service_name')
                record_errors = {}
                record_errors['service'] = service_name
                record_errors['reasons'] = []
                try:
                    facility = Facility.objects.get(code=facility_code)
                    try:
                        service = Service.objects.get(name=service_name)
                    except Service.DoesNotExist:
                        record_errors['reasons'].append(
                            'The linked service is missing'
                        )
                        errors.append(record_errors)
                        continue

                except Facility.DoesNotExist:
                    record_errors['reasons'].append(
                        'The linked facility is missing'
                    )
                    errors.append(record_errors)
                    continue

                print FacilityService.objects.create(
                    facility=facility, service=service,
                    created_by=system_user, updated_by=system_user)

        excel_file = open('facility_service_errors.xlsx', 'wb+')
        excel_file.write(_write_excel_file(errors))
        excel_file.close()
