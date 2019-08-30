import os
import json
from users.models import MflUser
from django.contrib.auth.models import Group
from django.conf import settings
from django.core.management import BaseCommand
from rest_framework.exceptions import ValidationError
from common.models import Contact, ContactType, County, UserContact, UserCounty

system_user = MflUser.objects.get(email='system@ehealth.or.ke')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # national users
        nationl_users_file = os.path.join(
            settings.BASE_DIR, 'data/new_data/demo/001000_users_national_admins.json')
        with open(nationl_users_file) as national_users_data_file:
            national_users_data = json.load(national_users_data_file)
            records = national_users_data[0].get('records')
            national_admins_group = Group.objects.get(name='National Administrators')
            for record in records:
                try:
                    user = MflUser.objects.get(username=record.get('user'))
                    user.groups.add(national_admins_group)
                    user.is_national = True
                    user.save()
                    print user
                except MflUser.DoesNotExist:
                    print "the requested user does not exist"
                    continue

        county_users_file = os.path.join(
            settings.BASE_DIR, 'data/new_data/demo/001002_users_chrios.json')
        with open(county_users_file) as county_users_data_file:
            chrio_users_data = json.load(county_users_data_file)
            records = chrio_users_data[0].get('records')
            chrio_group = Group.objects.get(name='County Health Records Information Officer')
            for record in records:
                try:
                    user = MflUser.objects.get(username=record.get('user'))
                    user.groups.add(chrio_group)
                    user.save()
                    print user
                except MflUser.DoesNotExist:
                    print "the requested user does not exist"
                    continue

        county_users_file = os.path.join(
            settings.BASE_DIR, 'data/new_data/demo/001002_users_counties.json')
        with open(county_users_file) as county_users_data_file:
            chrio_users_data = json.load(county_users_data_file)
            records = chrio_users_data[0].get('records')
            for record in records:
                try:
                    user = MflUser.objects.get(username=record.get('user'))
                    user.save()
                    print user
                    try:
                        county = County.objects.get(
                            name=record.get('county').upper())
                    except County.DoesNotExist:
                        print "County {0} does not exist".format(
                            record.get('county'))
                        continue

                    try:
                        user_county, created = UserCounty.objects.get_or_create(
                            county=county, user=user, created_by=system_user,
                            updated_by=system_user)
                    except ValidationError:
                        print "the user is already in that county"

                except MflUser.DoesNotExist:
                    print "the requested user does not exist"
                    continue

        super_users_file = os.path.join(
            settings.BASE_DIR, 'data/new_data/demo/001002_users_superusers.json')
        with open(super_users_file) as superusers_data_file:
            super_users_data = json.load(superusers_data_file)
            records = super_users_data[0].get('records')
            superusers_group = Group.objects.get(name='Superusers')
            for record in records:
                try:
                    user = MflUser.objects.get(username=record.get('user'))
                    user.groups.add(superusers_group)
                    user.is_superuser = True
                    user.save()
                    print user
                except MflUser.DoesNotExist:
                    print "the requested user does not exist"
                    continue

        #  load user phone contacts

        users_file = os.path.join(
            settings.BASE_DIR, 'data/new_data/demo/001003_users_phones.json')
        with open(users_file) as users_data_file:
            users_data = json.load(users_data_file)
            records = users_data[0].get('records')
            phone_type = ContactType.objects.get(name='MOBILE')
            for record in records:
                try:
                    user = MflUser.objects.get(username=record.get('user'))
                    phone_number = record.get('phone_number')
                    contact, created = Contact.objects.get_or_create(
                        contact=phone_number,
                        contact_type=phone_type, created_by=system_user,
                        updated_by=system_user)
                    uc, created = UserContact.objects.get_or_create(
                        contact=contact, user=user, created_by=system_user,
                        updated_by=system_user)
                    print uc
                except MflUser.DoesNotExist:
                    print "the requested user does not exist"
                    continue

        users_file = os.path.join(
            settings.BASE_DIR, 'data/new_data/demo/001004_users_emails.json')
        with open(users_file) as users_data_file:
            users_data = json.load(users_data_file)
            records = users_data[0].get('records')
            email_type = ContactType.objects.get(name='EMAIL')
            for record in records:
                try:
                    user = MflUser.objects.get(username=record.get('user'))
                    email = record.get('email')
                    contact, created = Contact.objects.get_or_create(
                        contact=email,
                        contact_type=email_type, created_by=system_user,
                        updated_by=system_user)
                    uc, created = UserContact.objects.get_or_create(
                        contact=contact, user=user, created_by=system_user,
                        updated_by=system_user)
                    print uc
                except MflUser.DoesNotExist:
                    print "the requested user does not exist"
                    continue
