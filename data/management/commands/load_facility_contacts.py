import os
import json

from common.models import Contact, ContactType
from facilities.models import (
    Facility, FacilityContact, Officer, OfficerContact
)
from users.models import MflUser

from django.core.management import BaseCommand
from django.conf import settings

system_user = MflUser.objects.get(email='system@ehealth.or.ke')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):

        # facility email contacts
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/email/0018_facility_emails_contacts.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            email_type = ContactType.objects.get(name='EMAIL')
            for record in records:
                conact = record.get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=conact,
                    contact_type=email_type
                )

        # facility email contacts linked
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/email/0019_facility_emails_contacts_linked.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            mobile_type = ContactType.objects.get(name='EMAIL')
            for record in records:
                contact = record.get('contact').get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=contact,
                    contact_type=mobile_type
                )
                facility = record.get('facility').get('code')
                try:
                    facility_obj = Facility.objects.get(code=facility)
                    print FacilityContact.objects.get_or_create(
                        contact=contact, facility=facility_obj,
                        created_by=system_user, updated_by=system_user)
                except Facility.DoesNotExist:
                    print "The requested facility does not exist"

        # officer email contacts
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/email/0030_officer_email_contacts.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            email_type = ContactType.objects.get(name='EMAIL')
            for record in records:
                conact = record.get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=conact,
                    contact_type=email_type
                )

        # officer email linked
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/email/0031_officer_email_contacts_linked.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            email_type = ContactType.objects.get(name='EMAIL')
            for record in records:
                contact = record.get('contact').get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=contact,
                    contact_type=email_type
                )
                officer = record.get('officer')
                if officer:
                    officer = officer.get('name')
                    try:
                        officer_obj = Officer.objects.filter(name=officer)
                        print OfficerContact.objects.get_or_create(
                            contact=contact, officer=officer_obj[0],
                            created_by=system_user, updated_by=system_user)
                    except IndexError:
                        print "The requested officer does not exist"
                else:
                    print "Officer key is missing"

        # facility fax contacts
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/fax/0022_facility_fax_contacts.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            email_type = ContactType.objects.get(name='FAX')
            for record in records:
                conact = record.get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=conact,
                    contact_type=email_type
                )

        # facility fax contacts linked
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/fax/0023_facility_fax_contacts_linked.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            mobile_type = ContactType.objects.get(name='FAX')
            for record in records:
                contact = record.get('contact').get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=contact,
                    contact_type=mobile_type
                )
                facility = record.get('facility').get('code')
                try:
                    facility_obj = Facility.objects.get(code=facility)
                    print FacilityContact.objects.get_or_create(
                        contact=contact, facility=facility_obj,
                        created_by=system_user, updated_by=system_user)
                except Facility.DoesNotExist:
                    print "The requested facility does not exist"

        # facility landline contacts
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/landline/0020_facility_landline_contacts.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            email_type = ContactType.objects.get(name='LANDLINE')
            for record in records:
                conact = record.get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=conact,
                    contact_type=email_type
                )
        # facility landline contacts linked
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/landline/0021_facility_landline_contacts_linked.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            mobile_type = ContactType.objects.get(name='LANDLINE')
            for record in records:
                contact = record.get('contact').get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=contact,
                    contact_type=mobile_type
                )
                facility = record.get('facility').get('code')
                try:
                    facility_obj = Facility.objects.get(code=facility)
                    print FacilityContact.objects.get_or_create(
                        contact=contact, facility=facility_obj,
                        created_by=system_user, updated_by=system_user)
                except Facility.DoesNotExist:
                    print "The requested facility does not exist"

        # facility mobile contacts
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/mobile/0024_facility_mobile_contacts.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            email_type = ContactType.objects.get(name='MOBILE')
            for record in records:
                conact = record.get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=conact,
                    contact_type=email_type
                )

        # facility mobile contacts linked
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/mobile/0025_facility_mobile_contacts_linked.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            mobile_type = ContactType.objects.get(name='MOBILE')
            for record in records:
                contact = record.get('contact').get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=contact,
                    contact_type=mobile_type
                )
                facility = record.get('facility').get('code')
                try:
                    facility_obj = Facility.objects.get(code=facility)
                    print FacilityContact.objects.get_or_create(
                        contact=contact, facility=facility_obj,
                        created_by=system_user, updated_by=system_user)
                except Facility.DoesNotExist:
                    print "The requested facility does not exist"

        # officers mobile contacts
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/mobile/0028_officer_mobile_contacts.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            email_type = ContactType.objects.get(name='MOBILE')
            for record in records:
                conact = record.get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=conact,
                    contact_type=email_type
                )

        # officer mobiles linked
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/new_data/mobile/0029_officer_mobile_contacts_linked.json'
        )
        with open(file_path) as email_contacts:
            email_data = json.load(email_contacts)
            records = email_data[0].get('records')
            email_type = ContactType.objects.get(name='MOBILE')
            for record in records:
                contact = record.get('contact').get('contact')
                contact, created = Contact.objects.get_or_create(
                    contact=contact,
                    contact_type=email_type
                )
                officer = record.get('officer')
                if officer:
                    officer = officer.get('name')
                    try:
                        officer_obj = Officer.objects.filter(name=officer)
                        print OfficerContact.objects.get_or_create(
                            contact=contact, officer=officer_obj[0],
                            created_by=system_user, updated_by=system_user)
                    except IndexError:
                        print "The requested officer does not exist"
                else:
                    print "Officer key is missing"
