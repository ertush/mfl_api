import os
import json
from facilities.models import Facility, FacilityApproval
from django.core.management import BaseCommand
from django.conf import settings
from users.models import MflUser


system_user = MflUser.objects.get(email='system@ehealth.or.ke')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/demo_part_2/00_facility_approvals.json')
        with open(file_path) as approvals_file:
            data = json.load(approvals_file)
            records = data[0].get('records')
            for record in records:
                facility_code = record.get('facility').get('code')

                try:
                    facility = Facility.objects.get(code=facility_code)
                    print FacilityApproval.objects.get_or_create(
                        facility=facility, created_by=system_user,
                        updated_by=system_user,
                        comment='Initial approval by system')

                except Facility.DoesNotExist:
                    print "The requested facility does not exist"
