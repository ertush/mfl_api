import os
import json
import xlrd


from django.conf import settings
from django.core.management import BaseCommand
from users.models import MflUser

from facilities.models import Service, ServiceCategory, OptionGroup

system_user = MflUser.objects.get(email='system@ehealth.or.ke')


class Command(BaseCommand):

    def read_sheet_content(self, sheet):

        sheet_content = []

        for k in range(1, 100):
            sheet_data = {}
            try:
                sheet_data['category'] = sheet.cell(k, 0).value
                sheet_data['sub_category'] = sheet.cell(k, 1).value
                sheet_data['service'] = sheet.cell(k, 2).value
                sheet_data['desc'] = sheet.cell(k, 3).value
                sheet_data['mode'] = sheet.cell(k, 4).value
                sheet_content.append(sheet_data)
            except IndexError:
                break
        return sheet_content

    def write_json_file(self, file_name, data):
        assert file_name
        assert not file_name == '/'
        assert not file_name == '.'

        if os.path.exists(file_name):
            os.remove(file_name)
        with open(file_name, 'w+') as data_file:
            json.dump(data, data_file, indent=4)

    def handle(self, *args, **kwargs):
        file_path = os.path.join(
            settings.BASE_DIR,
            'data/resources/service_catalogue.xlsx'
        )
        book = xlrd.open_workbook(file_path)
        number_of_sheets = book.nsheets
        categories = []
        services = []
        sub_categories = []

        # read the categories
        category_sheet = book.sheet_by_index(0)

        for y in range(3, 18):
            try:
                category = category_sheet.cell(y, 0).value
                categories.append(category)
            except IndexError:
                break

        for x in range(1, number_of_sheets + 1):

            try:
                sheet = book.sheet_by_index(x)
            except IndexError:
                break

            sheet_data = self.read_sheet_content(sheet)
            for item in sheet_data:
                if item.get('sub_category'):
                    sub_categories.append(
                        {
                            "name": item.get('sub_category'),
                            "parent": item.get('category')
                        }
                    )
                    services.append(
                        {
                            "name": item.get('service'),
                            "description": item.get('desc'),
                            "mode": item.get('mode'),
                            "category": item.get('sub_category')
                        }
                    )
                else:
                    services.append(
                        {
                            "name": item.get('service'),
                            "description": item.get('desc'),
                            "mode": item.get('mode'),
                            "category": item.get('category')
                        }
                    )

        yes_no_mode = OptionGroup.objects.get(
            name='Yes /No Options')
        b_c_mode = OptionGroup.objects.get(
            name='Basic Comprehensive Options')
        # categories
        for category in categories:
            try:
                ServiceCategory.objects.get(name=category)
            except:
                ServiceCategory.objects.create(
                    name=category, created_by=system_user,
                    updated_by=system_user)
        # sub_categories

        for category in sub_categories:
            try:
                ServiceCategory.objects.get(name=category.get('name'))
            except:
                try:
                    parent = ServiceCategory.objects.get(
                        name=category.get('parent'))
                except ServiceCategory.DoesNotExist:
                    parent = ServiceCategory.objects.create(
                        name=category.get('parent'), created_by=system_user,
                        updated_by=system_user)
                ServiceCategory.objects.create(
                    parent=parent,
                    name=category.get('name'),
                    created_by=system_user,
                    updated_by=system_user
                )
        # services
        for service in services:
            try:
                category = ServiceCategory.objects.get(
                    name=service.get('category'))
            except:
                if service.get('category'):

                    category = ServiceCategory.objects.create(
                        name=service.get('category'), created_by=system_user,
                        updated_by=system_user)

                else:
                    print "Category not provided"

            has_options = False
            mode = service.get('mode')

            if mode.find('Yes') > -1:
                mode = yes_no_mode
            elif mode.find('Comprehensive') > -1:
                mode = b_c_mode
                has_options = True
            elif mode.find('Basic') > -1:
                mode = b_c_mode
                has_options = True
            else:
                mode = yes_no_mode

            description = service.get('desc')

            try:
                Service.objects.get(name=service.get('name'))
            except Service.DoesNotExist:
                Service.objects.create(
                    name=service.get('name'),
                    category=category, description=description,
                    group=mode, has_options=has_options,
                    created_by=system_user, updated_by=system_user
                )

        # cats_file_path = os.path.join(
        #     settings.BASE_DIR,
        #     'data/resources/categories.json'
        # )
        # sub_cats_file_path = os.path.join(
        #     settings.BASE_DIR,
        #     'data/resources/sub_categories.json'
        # )
        # services_file_path = os.path.join(
        #     settings.BASE_DIR,
        #     'data/resources/services.json'
        # )
        # self.write_json_file(cats_file_path, categories)
        # self.write_json_file(sub_cats_file_path, sub_categories)
        # self.write_json_file(services_file_path, services)
