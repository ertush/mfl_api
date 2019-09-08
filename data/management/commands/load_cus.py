import json
import os

from chul.models import (
    CommunityHealthUnit,
    CommunityHealthUnitContact,
    Status,
    CommunityHealthWorker)
from users.models import MflUser
from facilities.models import Facility
from django.core.management import BaseCommand
from django.conf import settings
from common.models import ContactType, Contact
from dateutil.parser import parse
system_user = MflUser.objects.get(email='system@ehealth.or.ke')
email = ContactType.objects.get(name='EMAIL')
mobile = ContactType.objects.get(name='MOBILE')

from django.core.exceptions import ValidationError
from common.renderers.excel_renderer import _write_excel_file


class Command(BaseCommand):

    def handle(self, *args, **options):
        # def load_chus():
        data = 'data/new_data/mcul/00100_cus.json'
        data = os.path.join(settings.BASE_DIR, data)
        data_file = open(data)
        data = json.loads(data_file.read())
        records = data[0].get('records')
        f_missing = 0
        s_missing = 0
        found = 0
        cus_with_facility_errrors = []
        cus_with_status_errors = []
        cus_errors_due_date_errors = []
        validation_errors = []
        missing_facility_errors = []
        for record in records:
            unit_errors = {
                'unit_code': record.get('code'),
                'unit_name': record.get('name'),
                'linked_facility': record.get('facility').get('code'),
                'linked_facility_name': record.pop('facility_name', None),
                'error_reasons': [],
                "county": record.pop('county', None),
                "division": record.pop('division', None),

            }

            try:

                facility = Facility.objects.get(
                    code=record.get('facility').get('code'))
                chu_status = Status.objects.get(
                    name=record.get('status').get('name'))
                found += 1
            except (Facility.DoesNotExist):
                print "The facility {} could not be located".format(
                    record.get('facility').get('code'))
                cus_with_facility_errrors.append(record)
                unit_errors['error_reasons'].append(
                    'The chu facility has got errors, and thus was not migrated')
                missing_facility_errors.append(unit_errors)
                f_missing += 1
                continue

            except Status.DoesNotExist:
                s_missing += 1
                cus_with_status_errors.append(record)
                print "The status {} could not be located".format(
                    record.get('status').get('name'))
                continue
        # print f_missing, s_missing, found, len(records)
            non_existing_cus = 0
            existin_cus = 0
            households_monitored = record.get('households_monitored')
            if not households_monitored or households_monitored == '' or households_monitored == ' ':
                households_monitored = 0
            ch_data = {
                "name": record.get("name"),
                "code": record.get("code"),
                "facility": facility,
                "status": chu_status,
                "households_monitored": households_monitored,
                "location": record.get('location'),
                "created_by": system_user,
                "updated_by": system_user
            }
            if record.get('date_established'):
                ch_data['date_established'] = parse(
                    record.get('date_established'))
            if record.get('date_operational'):
                ch_data['date_operational'] = parse(
                    record.get('date_operational'))
            try:
                chu = CommunityHealthUnit.objects.get(code=ch_data.get('code'))
                non_existing_cus += 1
                print chu.name
                existin_cus += 1
                print "CHU with code {} already exists".format(record.get('code'))
                continue
            except CommunityHealthUnit.DoesNotExist:
                try:
                    chu = CommunityHealthUnit.objects.create(**ch_data)

                except ValidationError:
                    cus_errors_due_date_errors.append(record)
                    unit_errors['error_reasons'].append(
                        'Date date established is greater then date operational'
                    )
                    validation_errors.append(unit_errors)
                    continue

            print non_existing_cus, existin_cus
            # return
            cu_email = record.get('cu_email')
            cu_mobile = record.get('cu_mobile')
            if cu_email:
                con, created = Contact.objects.get_or_create(
                    contact=cu_email,
                    contact_type=email, created_by=system_user,
                    updated_by=system_user)
                print CommunityHealthUnitContact.objects.get_or_create(
                    contact=con, health_unit=chu,
                    created_by=system_user, updated_by=system_user)
            if cu_mobile:
                con, created = Contact.objects.get_or_create(
                    contact=cu_mobile,
                    contact_type=mobile)
                print CommunityHealthUnitContact.objects.get_or_create(
                    contact=con, health_unit=chu,
                    created_by=system_user, updated_by=system_user)
            #chew 1
            name = record.get('chew')
            chew_in_charge = record.get('chew_in_charge')

            if name:
                chew_data = {
                    "first_name": name,
                    "created_by": system_user,
                    "updated_by": system_user,
                    "health_unit": chu

                }
                print CommunityHealthWorker.objects.get_or_create(**chew_data)

            #chew 2
            if chew_in_charge:
                chew_data = {
                    "first_name": chew_in_charge,
                    "created_by": system_user,
                    "updated_by": system_user,
                    "health_unit": chu,
                    'is_incharge': True

                }
                print CommunityHealthWorker.objects.get_or_create(**chew_data)

        with open('cus_with_facility_errrors', 'w+') as error_cus_file:
            error_cus_file.write(json.dumps(cus_with_facility_errrors))

        with open('cus_with_status_errors', 'w+') as error_cus_file:
            error_cus_file.write(json.dumps(cus_with_status_errors))

        with open('cus_errors_due_date_errors', 'w+') as error_cus_file:
            error_cus_file.write(json.dumps(cus_errors_due_date_errors))

        excel_file = open('chu_with_errorneous_facilities.xlsx', 'wb+')
        excel_file.write(_write_excel_file(missing_facility_errors))
        excel_file.close()

        excel_file = open('chu_with_validation_errors.xlsx', 'wb+')
        excel_file.write(_write_excel_file(validation_errors))
        excel_file.close()

        # def dump_chus():
        #         print "Here"
        #         data = [
        #             {
        #                 "unique_fields": ["code"],
        #                 "model": "chul.CommunityHealthUnit",
        #                 "records": []
        #             }
        #         ]
        #         index = 0
        #         for chu in CommunityHealthUnit.objects.all():
        #             chu_data = {
        #                 "name": chu.name,
        #                 "code": chu.code,
        #                 "facility": {
        #                     "code": chu.facility.code
        #                 },
        #                 "status": {
        #                     "name": chu.status.name
        #                 },
        #                 "households_monitored": chu.households_monitored,
        #                 "location": chu.location
        #             }
        #             data[0]['records'].append(chu_data)
        #             print "Chu" + str(index)
        #             index += 1
        #         new_file = '/home/titan/savannah/mfl_api/data/data/mcul/00102_chus.json'

        #         with open(new_file, 'w+') as new_file_data:
        #             json.dump(data, new_file_data, indent=4)

        #         data = [
        #             {
        #                 "unique_fields": ["first_name", "health_unit", "id_number"],
        #                 "model": "chul.CommunityHealthWorker",
        #                 "records": []
        #             }
        #         ]
        #         index = 0
        #         for chew in CommunityHealthWorker.objects.all():
        #             chew_data = {
        #                 "first_name": chew.first_name,
        #                 "health_unit": {
        #                     "code": chew.health_unit.code
        #                 }
        #             }
        #             data[0]['records'].append(chew_data)
        #             print "chew" + str(index)
        #             index += 1

        #         new_file = '/home/titan/savannah/mfl_api/data/data/mcul/00103_chews.json'
        #         with open(new_file, 'w+') as new_file_data:
        #             json.dump(data, new_file_data, indent=4)

        #         data = [
        #             {
        #                 "unique_fields": ["contact", "health_unit"],
        #                 "model": "chul.CommunityHealthUnitContact",
        #                 "records": []
        #             }
        #         ]
        #         index = 0
        #         for con in CommunityHealthUnitContact.objects.all():
        #             if con.contact.contact != "NULL":
        #                 con_data = {
        #                     "contact": {
        #                         "contact": con.contact.contact

        #                     },
        #                     "contact_type": {
        #                         "contact_type": con.contact.contact_type.name
        #                     },
        #                     "health_unit": {
        #                         "code": con.health_unit.code
        #                     }
        #                 }
        #                 data[0]['records'].append(con_data)
        #             print "con" + str(index)
        #             index += 1
        #         new_file = '/home/titan/savannah/mfl_api/data/data/mcul/00104_cons.json'
        #         with open(new_file, 'w+') as new_file_data:
        #             json.dump(data, new_file_data, indent=4)

        # dump_chus()
