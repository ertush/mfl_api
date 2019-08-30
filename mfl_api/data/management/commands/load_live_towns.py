import os
import json

from django.core.management import BaseCommand
from django.conf import settings

from users.models import MflUser
from common.models import Town


system_user = MflUser.objects.get(email='system@ehealth.or.ke')


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # file_path = os.path.join(
        #     settings.BASE_DIR, 'data/new_data/demo/0014_live_towns.json')
        # with open(file_path) as data:
        #     records = json.loads(data.read())[0].get('records')
        #     for record in enumerate(records):
        #         try:
        #             Town.objects.get(name=record[1].get('name'))
        #         except Town.DoesNotExist:
        #             Town.objects.create(
        #                 name=record[1].get('name'),
        #                 created_by=system_user,
        #                 updated_by=system_user
        #             )
        #             print str(record[0]) + '/' + str(len(records))

        file_path = os.path.join(
            settings.BASE_DIR, 'data/new_data/demo/0014_live_missed_towns.json')
        with open(file_path) as data:
            records = json.loads(data.read())[0].get('records')
            for record in enumerate(records):
                try:
                    Town.objects.get(name=record[1].get('name'))
                except Town.DoesNotExist:
                    Town.objects.create(
                        name=record[1].get('name'),
                        created_by=system_user,
                        updated_by=system_user
                    )
                    print str(record[0]) + '/' + str(len(records))


