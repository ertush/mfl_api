#!/usr/bin/env python

import os
import json
import logging

from django.conf import settings
from django.template import loader, Context
from django.contrib.auth.models import make_password

import sqlalchemy as sa


DEFAULT_DB = "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_public?driver=freetds"  # NOQA
LOGGER = logging.getLogger(__name__)


class Database(object):
    def _init__(self, connection_string=DEFAULT_DB):
        self.engine = sa.create_engine(connection_string)

    def read_db_object(self, sql):
        return self.engine.execute(sql)


class CreateJsonFiles(object):
    """
    A class that creates the json data files from MFL version 1.

    These data files will be consumed in data bootstrap where
    they will be loaded into the db.
    """
    database = Database()

    def _help_create_file(
            self, folder_type, file_name, model_name, unique_fields, data):
        """
        Helper method to create json files

        Removes a file if it exists and recreates it again
        """
        file_path = os.path.join(folder_type, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)
        with open(file_path, 'w+') as json_file:
            template = loader.get_template('json_file_template.txt')
            context = Context(
                {
                    "model_name": model_name,
                    "unique_fields": unique_fields,
                    "records": data
                }
            )
            to_write = [
                {
                    "model": model_name,
                    "unique_fields": unique_fields,
                    "records": data
                }
            ]
            json_data = template.render(context)  # NOQA
            # 
            # 
            # json_file.write(json_data, indent=4)
            json.dump(to_write, json_file, indent=4)

    def create_single_json_file(
            self, file_name, folder, model_name, unique_fields, data,
            in_v1=True):
        """
        Creates a single json file
        """
        demo_folder = os.path.join(settings.BASE_DIR, "data/new_data/demo")
        demo_folder_2 = os.path.join(settings.BASE_DIR, "data/new_data/demo_part_2")
        setup_folder = os.path.join(settings.BASE_DIR, "data/new_data/setup")
        fax_folder = os.path.join(settings.BASE_DIR, "data/new_data/fax")
        email_folder = os.path.join(settings.BASE_DIR, "data/new_data/email")
        landline_folder = os.path.join(
            settings.BASE_DIR, "data/new_data/landline")
        mobile_folder = os.path.join(settings.BASE_DIR, "data/new_data/mobile")
        geo_code_folder = os.path.join(
            settings.BASE_DIR, "data/new_data/geocodes")
        mcul_folder = os.path.join(settings.BASE_DIR, "data/new_data/mcul")
        if folder == "demo":
            self._help_create_file(
                demo_folder, file_name, model_name, unique_fields, data)
        elif folder == "setup":
            self._help_create_file(
                setup_folder, file_name, model_name, unique_fields, data)
        elif folder == "demo2":
            self._help_create_file(
                demo_folder_2, file_name, model_name, unique_fields, data)
        elif folder == 'fax':
            self._help_create_file(
                fax_folder, file_name, model_name, unique_fields, data)
        elif folder == 'mobile':
            self._help_create_file(
                mobile_folder, file_name, model_name, unique_fields, data)
        elif folder == 'email':
            self._help_create_file(
                email_folder, file_name, model_name, unique_fields, data)
        elif folder == 'landline':
            self._help_create_file(
                landline_folder, file_name, model_name, unique_fields, data)
        elif folder == 'geocodes':
            self._help_create_file(
                geo_code_folder, file_name, model_name, unique_fields, data)
        elif folder == 'mcul':
            self._help_create_file(
                mcul_folder, file_name, model_name, unique_fields, data)
        else:
            raise Exception("The folder was given does not exist")

    def create_job_titles_json(self):
        file_name = "0000_job_titles.json"
        folder = "setup"
        model_name = "users.JobTitle"
        unique_fields = ["name"]
        data = []
        self.create_single_json_file(
            file_name, folder, model_name, unique_fields, data)


SETUP_DATA_CONFIG = [
{
        "resource_name": "Services",
        "mfl_v1_object_name": "[facility_services_through]",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "code",
                "v1_pos": 0
            },
             {
                "v1": "svcName",
                "v2": "service_name",
                "v1_pos": 1
            }
        ],
        "file_name": "00012_services.json",
        "folder": "setup",
        "model_name": "facilities.Service",
        "unique_fields": ['name'],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds",
        "sql": "SELECT Facility_Code, svcName FROM facility_services_through",
        "data": []
    },

{
        "resource_name": "Job Titles",
        "mfl_v1_object_name": "facility_codes",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "code",
                "v1_pos": 0
            }
        ],
        "file_name": "0001_facility_codes.json",
        "folder": "setup",
        "model_name": "users.JobTitle",
        "unique_fields": ['name'],
        "sql": "SELECT Facility_Code FROM facility_codes",
        "data": []
    },

    {
        "resource_name": "Job Titles",
        "mfl_v1_object_name": "lkpJobTitles",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "ttlName",
                "v2": "name",
                "v1_pos": 0
            }
        ],
        "file_name": "0000_job_titles.kjson",
        "folder": "setup",
        "model_name": "users.JobTitle",
        "unique_fields": ['name'],
        "sql": "SELECT DISTINCT ttlName FROM lkpJobTitles",
        "data": []
    },
    {
        "resource_name": "Contact Types",
        "mfl_v1_object_name": "N/A",
        "mfl_v1_v2_fields_map": [],
        "file_name": "0001_contact_types.json",
        "folder": "setup",
        "model_name": "common.ContactType",
        "unique_fields": ["name"],
        "data": [
            {
                "name": "EMAIL"
            },
            {
                "name": "MOBILE"
            },
            {
                "name": "LANDLINE"
            },
            {
                "name": "FAX"
            },
            {
                "name": "POSTAL"
            }
        ]
    },
    {
        "resource_name": "Facility Operation Statuses",
        "mfl_v1_object_name": "lkpFacilityStatus",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "staShortName",
                "v1_pos": 0,
                "v2": "name"
            }
        ],
        "file_name": "0002_facility_operation_status.json",
        "folder": "setup",
        "model_name": "facilities.FacilityStatus",
        "unique_fields": ["name"],
        "data": [],
        "sql": "SELECT staName from lkpFacilityStatus"
    },
    {
        "resource_name": "Facility Types",
        "mfl_v1_object_name": "lkpFacilityTypes",
        "mfl_v1_v2_fields_map": [
            {
                 "v1": "typName",
                "v2": "name",
                "v1_pos": 0
            },
            # {
            #     "v1": "typShortName",
            #     "v2": "abbreviation",
            #     "v1_pos": 1
            # }
        ],
        "file_name": "0003_facility_types.json",
        "folder": "setup",
        "model_name": "facilities.FacilityType",
        "unique_fields": ["name"],
        "sql": "SELECT DISTINCT typName  from lkpFacilityTypes", # NOQA
        "data": []
    },
    {
        "resource_name": "Facility Owner Types",
        "mfl_v1_object_name": "lkpFacilityOwners",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "ownName",
                "v2": "name",
                "v1_pos": 0
            },
            # {
            #     "v1": "ownShortName",
            #     "v2": "abbreviation",
            #     "v1_pos": 1
            # }
        ],
        "file_name": "0004_facility_owner_types.json",
        "folder": "setup",
        "model_name": "facilities.OwnerType",
        "unique_fields": ["name"],
        "data": [],
        "sql": "SELECT  DISTINCT ownName, ownParent FROM  lkpFacilityOwners WHERE ownParent=0",  # NOQA
    },
    {
        "resource_name": "Facility Owners",
        "mfl_v1_object_name": "facility_owners_view",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "ownName",
                "v2": "name",
                "v1_pos": 0
            },
            {
                "v1": "parent_name",
                "v2": "owner_type",
                "v1_pos": 1,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0005_facility_owners.json",
        "folder": "setup",
        "model_name": "facilities.Owner",
        "unique_fields": ["name", "owner_type"],
        "data": [],
        "sql": "SELECT DISTINCT ownName, parent_name FROM facility_owners_view"
    },
    {
        "resource_name": "Regulators",
        "mfl_v1_object_name": "lkpRegulators",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "regName",
                "v1_pos": 2,
                "v2": "name"
            },
            {
                "v1": "regshortName",
                "v1_pos": 1,
                "v2": "abbreviation"
            },
            {
                "v1": "regFunctionVerb",
                "v1_pos": 8,
                "v2": "regulation_verb"
            },
            {
                "v1": "regDefaultStatus",
                "v1_pos": 6,
                "v2": "default_status",
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }

        ],
        "file_name": "0010_regulatory_bodies.json",
        "folder": "setup",
        "model_name": "facilities.RegulatingBody",
        "unique_fields": ["name"],
        "data": []
    },
    {
        "resource_name": "KEPH levels",
        "mfl_v1_object_name": "lkpKephLevels",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "kphName",
                "v1_pos": 2,
                "v2": "name"
            }
        ],
        "file_name": "0007_keph_levels.json",
        "folder": "setup",
        "model_name": "facilities.KephLevel",
        "unique_fields": ["name"],
        "data": []
    },
    {
        "resource_name": "Geo CodeMethods",
        "mfl_v1_object_name": "lkpGeoCodeMethod",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "geoName",
                "v1_pos": 0,
                "v2": "name"
            }
        ],
        "file_name": "0008_geo_code_methods.json",
        "folder": "setup",
        "model_name": "mfl_gis.GeoCodeMethod",
        "unique_fields": ["name"],
        "sql": "SELECT LTRIM(RTRIM(geoName)) FROM lkpGeoCodeMethod WHERE geoName <> NULL",  # NOQA
        "data": []
    },
    {
        "resource_name": "Geo CodeSources",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Source_of_Geo_Code",
                "v1_pos": 0,
                "v2": "name"
            }
        ],
        "file_name": "0009_geo_code_sources.json",
        "folder": "setup",
        "model_name": "mfl_gis.GeoCodeSource",
        "unique_fields": ["name"],
        "data": [],
        "sql": "SELECT DISTINCT LTRIM(RTRIM(Source_of_GeoCode)) from qryFacilities WHERE Source_of_GeoCode <> NULL "  # NOQA
    },
    {
        "resource_name": "Regulation Statuses",
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_regulator?driver=freetds", # NOQA
        "mfl_v1_object_name": "lkpRegulatorStatus",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "regStatusName",
                "v1_pos": 1,
                "v2": "name"
            }
        ],
        "file_name": "0006_regulatory_statuses.json",
        "folder": "setup",
        "model_name": "facilities.RegulationStatus",
        "unique_fields": ["name"],
        "data": [
            {"name": "Registered"},
            {"name": "Licensed"},
            {"name": "Gazetted"},
            {"name": "Pending Registration"},
            {"name": "Pending License"},
            {"name": "Pending Gazettement"}
        ]
    },
    # {
    #     "resource_name": "Counties",
    #     "mfl_v1_object_name": "N/A",
    #     "mfl_v1_v2_fields_map": [],
    #     "file_name": "0011_counties.json",
    #     "folder": "setup",
    #     "model_name": "common.County",
    #     "unique_fields": ["code"],
    #     "data": [],
    #     "data_file_path": os.path.join(
    #         settings.BASE_DIR, 'data/data/v2_data/0001_counties.json')
    # },
    # {
    #     "resource_name": "Constituencies",
    #     "mfl_v1_object_name": "N/A",
    #     "mfl_v1_v2_fields_map": [],
    #     "file_name": "0012_constituencies.json",
    #     "folder": "setup",
    #     "model_name": "common.Constituency",
    #     "unique_fields": ["code"],
    #     "data": [],
    #     "data_file_path": os.path.join(
    #         settings.BASE_DIR, 'data/data/v2_data/0002_constituencies.json')
    # },
    # {
    #     "resource_name": "Wards",
    #     "mfl_v1_object_name": "N/A",
    #     "mfl_v1_v2_fields_map": [],
    #     "file_name": "0013_wards.json",
    #     "folder": "setup",
    #     "model_name": "common.Ward",
    #     "unique_fields": ["code"],
    #     "data": [],
    #     "data_file_path": os.path.join(
    #         settings.BASE_DIR, 'data/data/v2_data/0009_wards.json')
    # },
    {
        "resource_name": "Towns",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Nearest_Town",
                "v2": "name",
                "v1_pos": 0
            }
        ],
        "file_name": "0014_towns.json",
        "folder": "demo",
        "model_name": "common.Town",
        "unique_fields": ["name"],
        "data": [],
        "sql": "SELECT DISTINCT LOWER(LTRIM(RTRIM(Facility_Nearest_Town))) from qryFacilities WHERE Facility_Nearest_Town <> NULL"  # NOQA
    },
    {
        "resource_name": "Facilities",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "code",
                "v1_pos": 0
            },
            {
                "v1": "Facility_Name",
                "v2": "name",
                "v1_pos": 1
            },
            {
                "v1": "Facility_Official_Name",
                "v2": "official_name",
                "v1_pos": 2
            },

            {
                "v1": "Date_Added",
                "v2": "created",
                "v1_pos": 8
            },
            {
                "v1": "Facility_Nearest_Town",
                "v2": "town",
                "v1_pos": 3,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Location_Description",
                "v2": "location_desc",
                "v1_pos": 5
            },
            {
                "v1": "Facility_Plot_Number",
                "v2": "plot_number",
                "v1_pos": 4
            },

            {
                "v1": "Num_Bed",
                "v2": "number_of_beds",
                "v1_pos": 10
            },
            {
                "v1": "Num_Cots",
                "v2": "number_of_cots",
                "v1_pos": 11
            },
            {
                "v1": "typName",
                "v2": "facility_type",
                "v1_pos": 12,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "ownName",
                "v2": "owner",
                "v1_pos": 13,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "kphName",
                "v2": "keph_level",
                "v1_pos": 14,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "regName",
                "v2": "regulatory_body",
                "v1_pos": 15,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "staDisplayName",
                "v2": "operation_status",
                "v1_pos": 16,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Facility_latitude",
                "v2": "latitude",
                "v1_pos": 17
            },
            {
                "v1": "facility_longitude",
                "v2": "longitude",
                "v1_pos": 18
            },
            {
                "v1": "prvName",
                "v2": "county",
                "v1_pos": 19
            },
            {
                "v1": "Facility_Division",
                "v2": "division",
                "v1_pos": 20
            },

        ],
        "file_name": "0016_facilities.json",
        "folder": "demo",
        "model_name": "facilities.Facility",
        "unique_fields": ["code"],
        "data": [],
        "sql": ("SELECT Facility_Code, Facility_Name, Facility_Official_Name, LOWER(LTRIM(RTRIM(Facility_Nearest_Town))), LOWER(LTRIM(RTRIM(Facility_Plot_Number))), Location_Description, Open24Hours, OpenWeekends, CONVERT(VARCHAR, Date_Added, 126), Date_Modified, Num_Beds, Num_Cots, typName, ownName, kphName, regName, staDisplayName,Facility_latitude, facility_longitude, prvName, Facility_Division from qryFacilities;")  # NOQA
    },
    # {
    #     "resource_name": "Facilities in the login site",
    #     "mfl_v1_object_name": "qryFacilities",
    #     "mfl_v1_v2_fields_map": [
    #         {
    #             "v1": "Facility_Code",
    #             "v2": "code",
    #             "v1_pos": 0
    #         },
    #         {
    #             "v1": "Facility_Name",
    #             "v2": "name",
    #             "v1_pos": 1
    #         },
    #         {
    #             "v1": "Facility_Official_Name",
    #             "v2": "official_name",
    #             "v1_pos": 2
    #         },

    #         {
    #             "v1": "Date_Added",
    #             "v2": "created",
    #             "v1_pos": 8
    #         },
    #         {
    #             "v1": "Facility_Nearest_Town",
    #             "v2": "town",
    #             "v1_pos": 3,
    #             "fk_map": [
    #                 {
    #                     "field_name": "name"
    #                 }
    #             ]
    #         },
    #         {
    #             "v1": "Location_Description",
    #             "v2": "location_desc",
    #             "v1_pos": 5
    #         },
    #         {
    #             "v1": "Facility_Plot_Number",
    #             "v2": "plot_number",
    #             "v1_pos": 4
    #         },

    #         {
    #             "v1": "Num_Bed",
    #             "v2": "number_of_beds",
    #             "v1_pos": 10
    #         },
    #         {
    #             "v1": "Num_Cots",
    #             "v2": "number_of_cots",
    #             "v1_pos": 11
    #         },
    #         {
    #             "v1": "typName",
    #             "v2": "facility_type",
    #             "v1_pos": 12,
    #             "fk_map": [
    #                 {
    #                     "field_name": "name"
    #                 }
    #             ]
    #         },
    #         {
    #             "v1": "ownName",
    #             "v2": "owner",
    #             "v1_pos": 13,
    #             "fk_map": [
    #                 {
    #                     "field_name": "name"
    #                 }
    #             ]
    #         },
    #         {
    #             "v1": "kphName",
    #             "v2": "keph_level",
    #             "v1_pos": 14,
    #             "fk_map": [
    #                 {
    #                     "field_name": "name"
    #                 }
    #             ]
    #         },
    #         {
    #             "v1": "regName",
    #             "v2": "regulatory_body",
    #             "v1_pos": 15,
    #             "fk_map": [
    #                 {
    #                     "field_name": "name"
    #                 }
    #             ]
    #         },
    #         {
    #             "v1": "staDisplayName",
    #             "v2": "operation_status",
    #             "v1_pos": 16,
    #             "fk_map": [
    #                 {
    #                     "field_name": "name"
    #                 }
    #             ]
    #         },
    #         {
    #             "v1": "Facility_latitude",
    #             "v2": "latitude",
    #             "v1_pos": 17
    #         },
    #         {
    #             "v1": "facility_longitude",
    #             "v2": "longitude",
    #             "v1_pos": 18
    #         },
    #          {
    #             "v1": "prvName",
    #             "v2": "county",
    #             "v1_pos": 19
    #         },


    #     ],
    #     "file_name": "0017_facilities.json",
    #     "folder": "demo",
    #     "model_name": "facilities.Facility",
    #     "unique_fields": ["code"],
    #     "data": [],
    #     "sql": ("SELECT Facility_Code, Facility_Name, Facility_Official_Name, LOWER(LTRIM(RTRIM(Facility_Nearest_Town))), LOWER(LTRIM(RTRIM(Facility_Plot_Number))), Location_Description, Open24Hours, OpenWeekends, CONVERT(VARCHAR, Date_Added, 126), Date_Modified, Num_Beds, Num_Cots, typName, ownName, kphName, regName, staDisplayName,Facility_latitude, facility_longitude, prvName from login_facilities;")  # NOQA
    # },
    {
        "resource_name": "users",
        "mfl_v1_object_name": "users_unique_by_mail_and_username",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "usrName",
                "v2": "username",
                "v1_pos": 0
            },
            {
                "v1": "usrFullName",
                "v2": "first_name",
                "v1_pos": 1
            },
            {
                "v1": "usrEmailAdd",
                "v2": "email",
                "v1_pos": 2
            },
            {
                "v1": "usrActive",
                "v2": "is_active",
                "v1_pos": 3
            },
            {
                "v1": "usrDateAdded",
                "v2": "date_joined",
                "v1_pos": 4
            },
            {
                "v1": "usrName",
                "v2": "employee_number",
                "v1_pos": 0
            },
            {
                "v1": "usrName",
                "v2": "password",
                "v1_pos": 0,
                "is_password": True
            }
        ],
        "file_name": "00999_users.json",
        "folder": "demo",
        "model_name": "users.MflUser",
        "unique_fields": ["username"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(usrName)),LTRIM(RTRIM(usrFullName)), LTRIM(RTRIM(usrEmailAdd)),LTRIM(RTRIM(usrActive)),CONVERT(VARCHAR, usrDateAdded, 126) FROM users_unique_by_mail_and_username WHERE usrName <> '8'"
    },
    {
        "resource_name": "users groups",
        "mfl_v1_object_name": "administrator_users",
        "mfl_v1_v2_fields_map": [
            {
                "user_field": "usrName",
                "user_field_pos": 0,
                "group_field": "grpName",
                "group": "group",
                "group_field_name": "National Administrators",
                "group_field_pos": 1,
                "is_user_group": True
            }

        ],
        "file_name": "001000_users_national_admins.json",
        "folder": "demo",
        "is_user_group": True,
        "model_name": "users.MflUser",
        "unique_fields": ["username"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(usrName)), LTRIM(RTRIM(usrName)) FROM administrator_users WHERE usrName <> '8'"
    },
    {
        "resource_name": "users groups",
        "mfl_v1_object_name": "user_counties",
        "mfl_v1_v2_fields_map": [
            {
                "user_field": "usrName",
                "user_field_pos": 0,
                "group_field": "prvName",
                "group_field_name": "County Health Records Information Officer",
                "group_field_pos": 1,
                "is_user_group": True
            }

        ],
        "file_name": "001002_users_chrios.json",
        "folder": "demo",
        "is_user_group": True,
        "model_name": "users.MflUser",
        "unique_fields": ["username"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(usrName)), LTRIM(RTRIM(usrName)) FROM user_counties WHERE  usrName <> '8'"
    },
    {
        "resource_name": "users groups",
        "mfl_v1_object_name": "superusers",
        "mfl_v1_v2_fields_map": [
            {
                "user_field": "usrName",
                "user_field_pos": 0,
                "group_field": "grpName",
                "group_field_name": "Superusers",
                "group_field_pos": 2,
                "is_user_group": True
            }

        ],
        "file_name": "001002_users_superusers.json",
        "folder": "demo",
        "is_user_group": True,
        "model_name": "users.MflUser",
        "unique_fields": ["username"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(usrName)), LTRIM(RTRIM(usrName)) FROM superusers WHERE usrName <> '8'"
    },

    {
        "resource_name": "users user_counties",
        "mfl_v1_object_name": "user_counties",
        "mfl_v1_v2_fields_map": [
            {
                "user_field": "usrName",
                "user_field_pos": 0,
                "county_field": "prvName",
                "county_name_pos": 1,
                "is_user_county": True
            }

        ],
        "file_name": "001002_users_counties.json",
        "folder": "demo",
        "is_user_group": True,
        "model_name": "users.MflUser",
        "unique_fields": ["username"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(usrName)), LTRIM(RTRIM(prvName)) FROM user_counties WHERE usrName <> '8'"
    },
    {
        "resource_name": "users phone numbers",
        "mfl_v1_object_name": "tblUsers",
        "mfl_v1_v2_fields_map": [
            {
                "user_field": "usrName",
                "user_field_pos": 0,
                "phone_no_pos": 1,
                "is_user_phone": True
            }

        ],
        "file_name": "001003_users_phones.json",
        "folder": "demo",
        "is_user_group": True,
        "model_name": "users.MflUser",
        "unique_fields": ["username"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(usrName)), LTRIM(RTRIM(usrPhoneNumber)) FROM tblUSers WHERE usrPhoneNumber <> NULL AND usrName <> '8'"
    },
    {
        "resource_name": "users Emails",
        "mfl_v1_object_name": "tblUsers",
        "mfl_v1_v2_fields_map": [
            {
                "user_field": "usrName",
                "user_field_pos": 0,
                "emal_pos": 1,
                "is_user_email": True
            }

        ],
        "file_name": "001004_users_emails.json",
        "folder": "demo",
        "is_user_group": True,
        "model_name": "users.MflUser",
        "unique_fields": ["username"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(usrName)), LTRIM(RTRIM(usrEmailAdd)) FROM tblUSers WHERE usrEmailAdd <> NULL"
    },
    {
        "resource_name": "MCUL Statuses",
        "mfl_v1_object_name": "cuStatus",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "staName",
                "v2": "name",
                "v1_pos": 0
            }

        ],
        "file_name": "00101_statuses.json",
        "folder": "mcul",
        "is_user_group": True,
        "model_name": "chul.Status",
        "unique_fields": ["name"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/mucl_login?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(staName))FROM cuStatus WHERE staName<> NULL"
    },
    {
        "resource_name": "MCUL",
        "mfl_v1_object_name": "community_units",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Cu_code",
                "v2": "code",
                "v1_pos": 0
            },
            {
                "v1": "CommUnitName",
                "v2": "name",
                "v1_pos": 1
            },
            {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 2,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]
            },
            {
                "v1": "CuLocation",
                "v2": "location",
                "v1_pos": 3
            },


            {
                "v1": "NumHouseHolds",
                "v2": "households_monitored",
                "v1_pos": 4
            },
            {
                "v1": "staName",
                "v2": "status",
                "v1_pos": 5,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Date_CU_Operational",
                "v2": "date_operational",
                "v1_pos": 6
            },
            {
                "v1": "CHEW_Facility",
                "v2": "chew",
                "v1_pos": 7
            },
            {
                "v1": "CHEW_In_Charge",
                "v2": "chew_in_charge",
                "v1_pos": 8
            },
            {
                "v1": "CU_OfficialMobile",
                "v2": "cu_mobile",
                "v1_pos": 9
            },
            {
                "v1": "CU_OfficialEmail",
                "v2": "cu_email",
                "v1_pos": 10
            },
            {
                "v1": "Date_CU_Established",
                "v2": "date_established",
                "v1_pos": 11
            },
            {
                "v1": "prvName",
                "v2": "county",
                "v1_pos": 12
            },
            {
                "v1": "facility_name",
                "v2": "facility_name",
                "v1_pos": 13
            },
            {
                "v1": "Facility_Division",
                "v2": "division",
                "v1_pos": 14
            },

        ],
        "file_name": "00100_cus.json",
        "folder": "mcul",
        "is_user_group": True,
        "model_name": "chul.CommunityHealthUnit",
        "unique_fields": ["code"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/mucl_login?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(Cu_code)), LTRIM(RTRIM(CommUnitName)), LTRIM(RTRIM(Facility_Code)), LTRIM(RTRIM(CuLocation)), LTRIM(RTRIM(NumHouseHolds)), LTRIM(RTRIM(staName)), CONVERT(VARCHAR, Date_CU_Operational, 126), LTRIM(RTRIM(CHEW_Facility)), LTRIM(RTRIM(CHEW_In_Charge)), LTRIM(RTRIM(CU_OfficialMobile)), LTRIM(RTRIM(CU_OfficialEmail)),  CONVERT(VARCHAR, Date_CU_Established, 126), prvName, facility_name, Facility_Division FROM community_units"
    },
    {
        "resource_name": "Services Categories",
        "mfl_v1_object_name": "lkpFacilityServices",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "svcName",
                "v2": "name",
                "v1_pos": 1
            },
            {
                "v1": "svcShortName",
                "v2": "abbreviation",
                "v1_pos": 2
            }
        ],
        "file_name": "0017_services_categories.json",
        "folder": "demo",
        "model_name": "facilities.ServiceCategory",
        "unique_fields": ["name"],
        "data": [],
        "sql": "SELECT svcId,svcName,svcShortName, svcParent from lkpFacilityServices  WHERE svcParent = 0"  # NOQA
    },
    {
        "resource_name": "Services",
        "mfl_v1_object_name": "facility_services_view",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "svcName",
                "v2": "name",
                "v1_pos": 1
            },
            {
                "v1": "svcShortName",
                "v2": "abbreviation",
                "v1_pos": 2
            },
            {
                "v1": "svcParent",
                "v2": "category",
                "v1_pos": 4,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0017_services.json",
        "folder": "demo",
        "model_name": "facilities.Service",
        "unique_fields": ["name"],
        "data": [],
        "sql": "SELECT svcId, svcName,svcShortName,svcParent, parent_name from facility_services_view  WHERE svcId <> 0"  # NOQA
    },
    {
        "resource_name": "Facility Email Contacts non linked",
         "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Official_Email",
                "v2": "contact",
                "v1_pos": 0
            },
            {
                "v1": "N/A",
                "v2": "contact_type",
                "v1_pos": 0,
                "v2_value": "EMAIL",
                "v2_name": "name",
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0018_facility_emails_contacts.json",
        "folder": "email",
        "model_name": "common.Contact",
        "unique_fields": ["contact", "contact_type"],
        "data": [],
        "sql": 'SELECT DISTINCT LTRIM(RTRIM(Official_Email)), Facility_Code, Facility_Name from qryFacilities where Official_Email <> NULL AND Official_Email <> "N/a" AND Official_Email <> "0" AND Official_Email <> "" AND Official_Email <> "none"  AND Official_Email <> "\\" AND Facility_Code <> NULL AND Facility_Name <> NULL'  # NOQA
    },
    {
        "resource_name": "Facility Email Contacts linked",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]
            },
            {
                "v1": "Official_Email",
                "v2": "contact",
                "v1_pos": 1,
                "fk_map": [
                    {
                        "field_name": "contact"
                    }
                ]
            }
        ],
        "file_name": "0019_facility_emails_contacts_linked.json",
        "folder": "email",
        "model_name": "facilities.FacilityContact",
        "unique_fields": ["facility", "contact"],
        "data": [],
        "sql": "SELECT DISTINCT Facility_Code, LTRIM(RTRIM(Official_Email)), Facility_Name from qryFacilities where Official_Email <> NULL AND Official_Email <> 'none' AND Official_Email <> 'N/a' AND Official_Email <> '' AND Official_Email <> '0' AND Official_Email <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Facility Landline Contacts non linked",
         "mfl_v1_object_name": "tblFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Official_Landline",
                "v2": "contact",
                "v1_pos": 0
            },
            {
                "v1": "N/A",
                "v2": "contact_type",
                "v1_pos": 0,
                "v2_value": "LANDLINE",
                "v2_name": "name",
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0020_facility_landline_contacts.json",
        "folder": "landline",
        "model_name": "common.Contact",
        "unique_fields": ["contact", "contact_type"],
        "data": [],
        "sql": "SELECT DISTINCT LTRIM(RTRIM(Official_Landline)) from qryFacilities where Official_Landline <> NULL AND Official_Landline <> '00000000' AND Official_Landline <> '0000000'  AND Official_Landline <> '00000' AND Official_Landline <>'0000' AND Official_Landline <> 'none' AND Official_Landline <> 'N/a' AND Official_Landline <> '' AND Official_Landline <> '0' AND Official_Landline <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Facility Landline Contacts linked",
        "mfl_v1_object_name": "tblFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]
            },
            {
                "v1": "Official_Landline",
                "v2": "contact",
                "v1_pos": 1,
                "fk_map": [
                    {
                        "field_name": "contact"
                    }
                ]
            }
        ],
        "file_name": "0021_facility_landline_contacts_linked.json",
        "folder": "landline",
        "model_name": "facilities.FacilityContact",
        "unique_fields": ["facility", "contact"],
        "data": [],
        "sql": "SELECT DISTINCT Facility_Code, LTRIM(RTRIM(Official_Landline)) from qryFacilities where Official_Landline <> NULL AND Official_Landline <> '00000000' AND Official_Landline <> '0000000'  AND Official_Landline <> '00000' AND Official_Landline <>'0000' AND Official_Landline <> 'none' AND Official_Landline <> 'N/a' AND Official_Landline <> '' AND Official_Landline <> '0' AND Official_Landline <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Facility FAX Contacts non linked",
         "mfl_v1_object_name": "tblFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Official_Fax",
                "v2": "contact",
                "v1_pos": 0
            },
            {
                "v1": "N/A",
                "v2": "contact_type",
                "v1_pos": 0,
                "v2_value": "FAX",
                "v2_name": "name",
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0022_facility_fax_contacts.json",
        "folder": "fax",
        "model_name": "common.Contact",
        "unique_fields": ["contact", "contact_type"],
        "data": [],
        "sql": "SELECT DISTINCT LTRIM(RTRIM(Official_Fax)) from qryFacilities where Official_Fax <> NULL AND Official_Fax <> '00000000' AND Official_Fax <>'00000000000' AND Official_Fax <> '0000000'  AND Official_Fax <> '-'  AND Official_Fax <> '00000' AND  Official_Fax <> '000' AND Official_Fax <>'0000' AND Official_Fax <> 'none' AND Official_Fax <> '00' AND Official_Fax <> 'N/a' AND Official_Fax <> '' AND Official_Fax <> '0' AND Official_Fax <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Facility FAX Contacts linked",
        "mfl_v1_object_name": "tblFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]
            },
            {
                "v1": "Official_Fax",
                "v2": "contact",
                "v1_pos": 1,
                "fk_map": [
                    {
                        "field_name": "contact"
                    }
                ]
            }
        ],
        "file_name": "0023_facility_fax_contacts_linked.json",
        "folder": "fax",
        "model_name": "facilities.FacilityContact",
        "unique_fields": ["facility", "contact"],
        "data": [],
        "sql": "SELECT DISTINCT Facility_Code, LTRIM(RTRIM(Official_Fax)) from qryFacilities where Official_Fax <> NULL AND Official_Fax <> '00000000'  AND Official_Fax <>'00000000000'  AND Official_Fax <> '-' AND Official_Fax <> '0000000'  AND Official_Fax <> '00000' AND Official_Fax <>'0000' AND Official_Fax <> '000' AND Official_Fax <> '00' AND Official_Fax <> 'none' AND Official_Fax <> 'N/a' AND Official_Fax <> '' AND Official_Fax <> '0' AND Official_Fax <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Facility MOBILE Contacts non linked",
         "mfl_v1_object_name": "tblFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Official_Mobile",
                "v2": "contact",
                "v1_pos": 0
            },
            {
                "v1": "N/A",
                "v2": "contact_type",
                "v1_pos": 0,
                "v2_value": "MOBILE",
                "v2_name": "name",
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0024_facility_mobile_contacts.json",
        "folder": "mobile",
        "model_name": "common.Contact",
        "unique_fields": ["contact", "contact_type"],
        "data": [],
        "sql": "SELECT DISTINCT LTRIM(RTRIM(Official_Mobile)) from qryFacilities where Official_Mobile <> NULL AND Official_Mobile <> '00000000'  AND Official_Mobile <>'00000000000' AND Official_Mobile <>'000000000' AND Official_Mobile <> '0000000000' AND Official_Mobile <> '-' AND Official_Mobile <> '0000000'  AND Official_Mobile <> '00000' AND Official_Mobile <>'0000' AND Official_Mobile <> '000' AND Official_Mobile <> '00' AND Official_Mobile <> 'none' AND Official_Mobile <> 'N/a' AND Official_Mobile <> '' AND Official_Mobile <> '0' AND Official_Mobile <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Facility MOBILE Contacts linked",
        "mfl_v1_object_name": "tblFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]
            },
            {
                "v1": "Official_Mobile",
                "v2": "contact",
                "v1_pos": 1,
                "fk_map": [
                    {
                        "field_name": "contact"
                    }
                ]
            }
        ],
        "file_name": "0025_facility_mobile_contacts_linked.json",
        "folder": "mobile",
        "model_name": "facilities.FacilityContact",
        "unique_fields": ["facility", "contact"],
        "data": [],
        "sql": "SELECT DISTINCT Facility_Code, LTRIM(RTRIM(Official_Mobile)) from qryFacilities where Official_Mobile <> NULL AND Official_Mobile <> '00000000'  AND Official_Mobile <>'00000000000' AND Official_Mobile <> '0000000000' AND Official_Mobile <>'000000000' AND Official_Mobile <> '-' AND Official_Mobile <> '0000000'  AND Official_Mobile <> '00000' AND Official_Mobile <>'0000' AND Official_Mobile <> '000' AND Official_Mobile <> '00' AND Official_Mobile <> 'none' AND Official_Mobile <> 'N/a' AND Official_Mobile <> '' AND Official_Mobile <> '0' AND Official_Mobile <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Officers",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "In_Charge_Name",
                "v2": "name",
                "v1_pos": 0
            },
            {
                "v1": "In_Charge_National_ID",
                "v2": "id_number",
                "v1_pos": 2
            },
            {
                "v1": "ttlName",
                "v2": "job_title",
                "v1_pos": 1,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0026_officers.json",
        "folder": "demo",
        "model_name": "facilities.Officer",
        "unique_fields": ["name", "job_title"],
        "data": [],
        "sql": "SELECT LTRIM(RTRIM(In_Charge_Name)), LTRIM(RTRIM(ttlName)), LTRIM(RTRIM(In_Charge_National_ID)) from qryFacilities WHERE In_Charge_Name <> NULL and ttlName <> NULL AND Facility_Code <> NULL AND Facility_Name <> NULL"   # NOQA
    },
    {
        "resource_name": "Facility Officers",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "In_Charge_Name",
                "v2": "officer",
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
             {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 3,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]
            }

        ],
        "file_name": "0027_facility_officers.json",
        "folder": "demo2",
        "model_name": "facilities.FacilityOfficer",
        "unique_fields": ["facility", "officer"],
        "data": [],
        "sql": "SELECT DISTINCT LTRIM(RTRIM(In_Charge_Name)), LTRIM(RTRIM(ttlName)), LTRIM(RTRIM(In_Charge_National_ID)), Facility_Code from qryFacilities WHERE In_Charge_Name <> NULL and ttlName <> NULL AND Facility_Code <> NULL AND Facility_Name <> NULL"   # NOQA
    },
    {
        "resource_name": "Officer Mobile Non Linked",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "In_Charge_Mobile",
                "v1_pos": 0,
                "v2": "contact"
            },
            {
                "v1": "N/A",
                "v2": "contact_type",
                "v1_pos": 0,
                "v2_value": "MOBILE",
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0028_officer_mobile_contacts.json",
        "folder": "mobile",
        "model_name": "common.Contact",
        "unique_fields": ["contact", "contact_type"],
        "data": [],
        "sql": "SELECT LTRIM(RTRIM(In_Charge_Mobile)), LTRIM(RTRIM(In_Charge_Name))  from qryFacilities WHERE In_Charge_Name <> NULL AND In_Charge_Mobile <> NULL AND In_Charge_Mobile <> '00000000'  AND In_Charge_Mobile <>'00000000000'  AND In_Charge_Mobile <> '-' AND In_Charge_Mobile <> '0000000'  AND In_Charge_Mobile <> '00000' AND In_Charge_Mobile <>'0000' AND In_Charge_Mobile <> '000' AND In_Charge_Mobile <> '00' AND In_Charge_Mobile <> 'none' AND In_Charge_Mobile <> 'N/a' AND In_Charge_Mobile <> '' AND In_Charge_Mobile <> '0' AND In_Charge_Mobile <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Officer Mobile  Linked",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "In_Charge_Mobile",
                "v2": "contact",
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "contact"
                    }
                ]
            },
            {
                "v1": "In_Charge_Name",
                "v2": "officer",
                "v1_pos": 1,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0029_officer_mobile_contacts_linked.json",
        "folder": "mobile",
        "model_name": "facilities.OfficerContact",
        "unique_fields": ["contact", "contact_type"],
        "data": [],
        "sql": "SELECT LTRIM(RTRIM(In_Charge_Mobile)), LTRIM(RTRIM(In_Charge_Name)) from qryFacilities WHERE In_Charge_Name <> NULL AND In_Charge_Mobile <> NULL AND In_Charge_Mobile <> '00000000'  AND In_Charge_Mobile <>'00000000000'  AND In_Charge_Mobile <> '-' AND In_Charge_Mobile <> '0000000'  AND In_Charge_Mobile <> '00000' AND In_Charge_Mobile <>'0000' AND In_Charge_Mobile <> '000' AND In_Charge_Mobile <> '00' AND In_Charge_Mobile <> 'none' AND In_Charge_Mobile <> 'N/a' AND In_Charge_Mobile <> '' AND In_Charge_Mobile <> '0' AND In_Charge_Mobile <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Officer EMAIL Non Linked",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "In_Charge_Email",
                "v1_pos": 0,
                "v2": "contact"
            },
            {
                "v1": "N/A",
                "v2": "contact_type",
                "v1_pos": 0,
                "v2_value": "EMAIL",
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0030_officer_email_contacts.json",
        "folder": "email",
        "model_name": "common.Contact",
        "unique_fields": ["contact", "contact_type"],
        "data": [],
        "sql": "SELECT LTRIM(RTRIM(In_Charge_Email))  from qryFacilities WHERE In_Charge_Email <> NULL AND In_Charge_Email <> NULL AND In_Charge_Email <> '00000000'  AND In_Charge_Email <>'00000000000'  AND In_Charge_Email <> '-' AND In_Charge_Email <> '0000000'  AND In_Charge_Email <> '00000' AND In_Charge_Email <>'0000' AND In_Charge_Email <> '000' AND In_Charge_Email <> '00' AND In_Charge_Email <> 'none' AND In_Charge_Email <> 'N/a' AND In_Charge_Email <> '' AND In_Charge_Email <> '0' AND In_Charge_Email <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Officer EMAIL  Linked",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "In_Charge_Email",
                "v2": "contact",
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "contact"
                    }
                ]
            },
            {
                "v1": "In_Charge_Name",
                "v2": "officer",
                "v1_pos": 1,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            }
        ],
        "file_name": "0031_officer_email_contacts_linked.json",
        "folder": "email",
        "model_name": "facilities.OfficerContact",
        "unique_fields": ["contact", "contact_type"],
        "data": [],
        "sql": "SELECT LTRIM(RTRIM(In_Charge_Email)), LTRIM(RTRIM(In_Charge_Name)) from qryFacilities WHERE In_Charge_Email <> NULL AND In_Charge_Email <> NULL AND In_Charge_Email <> '00000000'  AND In_Charge_Email <>'00000000000'  AND In_Charge_Email <> '-' AND In_Charge_Email <> '0000000'  AND In_Charge_Email <> '00000' AND In_Charge_Email <>'0000' AND In_Charge_Email <> '000' AND In_Charge_Email <> '00' AND In_Charge_Email <> 'none' AND In_Charge_Email <> 'N/a' AND In_Charge_Email <> '' AND In_Charge_Email <> '0' AND In_Charge_Email <> '\\' AND Facility_Code <> NULL AND Facility_Name <> NULL"  # NOQA
    },
    {
        "resource_name": "Facility Approvals",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Approved",
                "v2": 'facility',
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]

            }
            ],
        "file_name": "00_facility_approvals.json",
        "folder": "demo2",
        "model_name": "facilities.FacilityApproval",
        "unique_fields": ["facility"],
        "data": [],
        "sql": "SELECT Facility_Code, Facility_Name, Approved FROM qryFacilities WHERE Facility_Code <> NULL AND Facility_Name <> NUll AND Approved=1"  # NOQA
    },
    {
        "resource_name": "Facility Coordinates",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility",
                "v2": 'facility',
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]

            },
            {
                "v1": "latitude",
                "v2": "latitude",
                "v1_pos": 1
            },
            {

                "v1": "longitude",
                "v2": "longitude",
                "v1_pos": 2
            },


            {
                "v1": "Source_of_GeoCode",
                "v2": "source",
                "v1_pos": 3
            },
            {
                "v1": "Date_Of_GeoCode",
                "v2": "collection_date",
                "v1_pos": 4
            },
            {
                "v1": "geoName",
                "v2": "method",
                "v1_pos": 5
            }
            ],
        "file_name": "facility_codes.json",
        "folder": "geocodes",
        "model_name": "facilities.FacilityApproval",
        "unique_fields": ["facility"],
        "data": [],
        "sql": "SELECT Facility_Code, Facility_latitude, facility_longitude, LTRIM(RTRIM(Source_of_GeoCode)), CONVERT(VARCHAR, Date_Of_GeoCode, 126), LTRIM(RTRIM(geoName)) FROM qryFacilities WHERE Facility_Code <> NULL AND Facility_Name <> NUll AND  Approved=1 AND Source_of_GeoCode <> NULL AND geoName <> NULL"  # NOQA
    },
    {
        "resource_name": "Facility Officers",
        "mfl_v1_object_name": "lkpJobTitles",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "In_Charge_Name",
                "v2": "officer",
                "v1_pos": 0
            },
            {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 1
            }
        ],
        "file_name": "0001_facility_officers.json",
        "folder": "demo2",
        "model_name": "facilities.FacilityOfficer",
        "unique_fields": ['name'],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT  In_Charge_Name, Facility_Code FROM facility_officers_view",
        "data": []
    },
    {
        "resource_name": "Hours of Operation",
        "mfl_v1_object_name": "lkpJobTitles",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 0
            },
            {
                "v1": "Open24Hours",
                "v2": "open_whole_day",
                "v1_pos": 1
            },
            {
                "v1": "OpenWeekends",
                "v2": "open_weekends",
                "v1_pos": 2
            }
        ],
        "file_name": "0001_facility_officers.json",
        "folder": "demo2",
        "model_name": "facilities.FacilityOfficer",
        "unique_fields": ['name'],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT  Facility_Code, Open24Hours, OpenWeekends FROM facility_hours_of_operattion",
        "data": []
    }

]


SETUP_DATA_CONFIG.extend(
    [
        {
        "resource_name": "Facilities in the login site",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "code",
                "v1_pos": 0
            },
            {
                "v1": "Facility_Name",
                "v2": "name",
                "v1_pos": 1
            },
            {
                "v1": "Facility_Official_Name",
                "v2": "official_name",
                "v1_pos": 2
            },

            {
                "v1": "Date_Added",
                "v2": "created",
                "v1_pos": 8
            },
            {
                "v1": "Facility_Nearest_Town",
                "v2": "town",
                "v1_pos": 3,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Location_Description",
                "v2": "location_desc",
                "v1_pos": 5
            },
            {
                "v1": "Facility_Plot_Number",
                "v2": "plot_number",
                "v1_pos": 4
            },

            {
                "v1": "Num_Bed",
                "v2": "number_of_beds",
                "v1_pos": 10
            },
            {
                "v1": "Num_Cots",
                "v2": "number_of_cots",
                "v1_pos": 11
            },
            {
                "v1": "typName",
                "v2": "facility_type",
                "v1_pos": 12,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "ownName",
                "v2": "owner",
                "v1_pos": 13,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "kphName",
                "v2": "keph_level",
                "v1_pos": 14,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "regName",
                "v2": "regulatory_body",
                "v1_pos": 15,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "staDisplayName",
                "v2": "operation_status",
                "v1_pos": 16,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Facility_latitude",
                "v2": "latitude",
                "v1_pos": 17
            },
            {
                "v1": "facility_longitude",
                "v2": "longitude",
                "v1_pos": 18
            },
            {
                "v1": "prvName",
                "v2": "county",
                "v1_pos": 19
            },
            {
                "v1": "Facility_Division",
                "v2": "division",
                "v1_pos": 20
            },


        ],
        "file_name": "0017_facilities.json",
        "folder": "demo",
        "model_name": "facilities.Facility",
        "unique_fields": ["code"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": ("SELECT Facility_Code, Facility_Name, Facility_Official_Name, LOWER(LTRIM(RTRIM(Facility_Nearest_Town))), LOWER(LTRIM(RTRIM(Facility_Plot_Number))), Location_Description, Open24Hours, OpenWeekends, CONVERT(VARCHAR, Date_Added, 126), Date_Modified, Num_Beds, Num_Cots, typName, ownName, kphName, regName, staDisplayName,Facility_latitude, facility_longitude, prvName, Facility_Division from login_facilities;")  # NOQA
    },
    {
        "resource_name": "Towns in the login site",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [

            {
                "v1": "Facility_Nearest_Town",
                "v2": "name",
                "v1_pos": 0,

            }
        ],

        "file_name": "0014_live_towns.json",
        "folder": "demo",
        "model_name": "common.Town",
        "unique_fields": ["name"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": ("SELECT LOWER(LTRIM(RTRIM(Facility_Nearest_Town))) from login_facilities where Facility_Nearest_Town <> NULL;")  # NOQA
    },
     {
        "resource_name": "Facility Coordinates",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility",
                "v2": 'facility',
                "v1_pos": 0,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]

            },
            {
                "v1": "latitude",
                "v2": "latitude",
                "v1_pos": 1
            },
            {

                "v1": "longitude",
                "v2": "longitude",
                "v1_pos": 2
            },

            {
                "v1": "Date_Of_GeoCode",
                "v2": "collection_date",
                "v1_pos": 3
            }
            ],
        "file_name": "live_facility_codes.json",
        "folder": "geocodes",
        "model_name": "facilities.FacilityApproval",
        "unique_fields": ["facility"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": "SELECT Facility_Code, Facility_latitude, facility_longitude, CONVERT(VARCHAR, Date_Of_GeoCode, 126) FROM login_facilities WHERE Facility_Code <> NULL AND Facility_Name <> NUll AND  Approved=1 AND Source_of_GeoCode <> NULL;"  # NOQA
    },
    {
        "resource_name": "Facilities in the login site",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "code",
                "v1_pos": 0
            },
            {
                "v1": "Facility_Name",
                "v2": "name",
                "v1_pos": 1
            },
            {
                "v1": "Facility_Official_Name",
                "v2": "official_name",
                "v1_pos": 2
            },

            {
                "v1": "Date_Added",
                "v2": "created",
                "v1_pos": 8
            },
            {
                "v1": "Facility_Nearest_Town",
                "v2": "town",
                "v1_pos": 3,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Location_Description",
                "v2": "location_desc",
                "v1_pos": 5
            },
            {
                "v1": "Facility_Plot_Number",
                "v2": "plot_number",
                "v1_pos": 4
            },

            {
                "v1": "Num_Bed",
                "v2": "number_of_beds",
                "v1_pos": 10
            },
            {
                "v1": "Num_Cots",
                "v2": "number_of_cots",
                "v1_pos": 11
            },
            {
                "v1": "typName",
                "v2": "facility_type",
                "v1_pos": 12,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "ownName",
                "v2": "owner",
                "v1_pos": 13,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "kphName",
                "v2": "keph_level",
                "v1_pos": 14,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "regName",
                "v2": "regulatory_body",
                "v1_pos": 15,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "staDisplayName",
                "v2": "operation_status",
                "v1_pos": 16,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Facility_latitude",
                "v2": "latitude",
                "v1_pos": 17
            },
            {
                "v1": "facility_longitude",
                "v2": "longitude",
                "v1_pos": 18
            },
            {
                "v1": "prvName",
                "v2": "county",
                "v1_pos": 19
            },
            {
                "v1": "Facility_Division",
                "v2": "division",
                "v1_pos": 20
            },


        ],
        "file_name": "0018_missed_live_facilities.json",
        "folder": "demo",
        "model_name": "facilities.Facility",
        "unique_fields": ["code"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": ("SELECT Facility_Code, Facility_Name, Facility_Official_Name, LOWER(LTRIM(RTRIM(Facility_Nearest_Town))), LOWER(LTRIM(RTRIM(Facility_Plot_Number))), Location_Description, Open24Hours, OpenWeekends, CONVERT(VARCHAR, Date_Added, 126), Date_Modified, Num_Beds, Num_Cots, typName, ownName, kphName, regName, staDisplayName,Facility_latitude, facility_longitude, prvName, Facility_Division from all_login_facilities_view;")  # NOQA
    },
     {
        "resource_name": "Towns in the login site",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [

            {
                "v1": "Facility_Nearest_Town",
                "v2": "name",
                "v1_pos": 0,

            }
        ],

        "file_name": "0014_live_missed_towns.json",
        "folder": "demo",
        "model_name": "common.Town",
        "unique_fields": ["name"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": ("SELECT LOWER(LTRIM(RTRIM(Facility_Nearest_Town))) from all_login_facilities_view where Facility_Nearest_Town <> NULL;")  # NOQA
    },
 ]
 )

NOT_SETUP_DATA_CONFIG = [
 {
        "resource_name": "MCUL",
        "mfl_v1_object_name": "community_units",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Cu_code",
                "v2": "code",
                "v1_pos": 0
            },
            {
                "v1": "CommUnitName",
                "v2": "name",
                "v1_pos": 1
            },
            {
                "v1": "Facility_Code",
                "v2": "facility",
                "v1_pos": 2,
                "fk_map": [
                    {
                        "field_name": "code"
                    }
                ]
            },
            {
                "v1": "CuLocation",
                "v2": "location",
                "v1_pos": 3
            },


            {
                "v1": "NumHouseHolds",
                "v2": "households_monitored",
                "v1_pos": 4
            },
            {
                "v1": "staName",
                "v2": "status",
                "v1_pos": 5,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Date_CU_Operational",
                "v2": "date_operational",
                "v1_pos": 6
            },
            {
                "v1": "CHEW_Facility",
                "v2": "chew",
                "v1_pos": 7
            },
            {
                "v1": "CHEW_In_Charge",
                "v2": "chew_in_charge",
                "v1_pos": 8
            },
            {
                "v1": "CU_OfficialMobile",
                "v2": "cu_mobile",
                "v1_pos": 9
            },
            {
                "v1": "CU_OfficialEmail",
                "v2": "cu_email",
                "v1_pos": 10
            },
            {
                "v1": "Date_CU_Established",
                "v2": "date_established",
                "v1_pos": 11
            },
            {
                "v1": "prvName",
                "v2": "county",
                "v1_pos": 12
            },
            {
                "v1": "facility_name",
                "v2": "facility_name",
                "v1_pos": 13
            },
            {
                "v1": "Facility_Division",
                "v2": "division",
                "v1_pos": 14
            },

        ],
        "file_name": "00100_cus.json",
        "folder": "mcul",
        "is_user_group": True,
        "model_name": "chul.CommunityHealthUnit",
        "unique_fields": ["code"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/mucl_login?driver=freetds", # NOQA
        "sql": "SELECT LTRIM(RTRIM(Cu_code)), LTRIM(RTRIM(CommUnitName)), LTRIM(RTRIM(Facility_Code)), LTRIM(RTRIM(CuLocation)), LTRIM(RTRIM(NumHouseHolds)), LTRIM(RTRIM(staName)), CONVERT(VARCHAR, Date_CU_Operational, 126), LTRIM(RTRIM(CHEW_Facility)), LTRIM(RTRIM(CHEW_In_Charge)), LTRIM(RTRIM(CU_OfficialMobile)), LTRIM(RTRIM(CU_OfficialEmail)),  CONVERT(VARCHAR, Date_CU_Established, 126), prvName, facility_name, Facility_Division FROM community_units"
    },]


SETUP_DATA_CONFIG = [
    {
        "resource_name": "Facilities in the login site",
        "mfl_v1_object_name": "qryFacilities",
        "mfl_v1_v2_fields_map": [
            {
                "v1": "Facility_Code",
                "v2": "code",
                "v1_pos": 0
            },
            {
                "v1": "Facility_Name",
                "v2": "name",
                "v1_pos": 1
            },
            {
                "v1": "Facility_Official_Name",
                "v2": "official_name",
                "v1_pos": 2
            },

            {
                "v1": "Date_Added",
                "v2": "created",
                "v1_pos": 8
            },
            {
                "v1": "Facility_Nearest_Town",
                "v2": "town",
                "v1_pos": 3,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Location_Description",
                "v2": "location_desc",
                "v1_pos": 5
            },
            {
                "v1": "Facility_Plot_Number",
                "v2": "plot_number",
                "v1_pos": 4
            },

            {
                "v1": "Num_Bed",
                "v2": "number_of_beds",
                "v1_pos": 10
            },
            {
                "v1": "Num_Cots",
                "v2": "number_of_cots",
                "v1_pos": 11
            },
            {
                "v1": "typName",
                "v2": "facility_type",
                "v1_pos": 12,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "ownName",
                "v2": "owner",
                "v1_pos": 13,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "kphName",
                "v2": "keph_level",
                "v1_pos": 14,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "regName",
                "v2": "regulatory_body",
                "v1_pos": 15,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "staDisplayName",
                "v2": "operation_status",
                "v1_pos": 16,
                "fk_map": [
                    {
                        "field_name": "name"
                    }
                ]
            },
            {
                "v1": "Facility_latitude",
                "v2": "latitude",
                "v1_pos": 17
            },
            {
                "v1": "facility_longitude",
                "v2": "longitude",
                "v1_pos": 18
            },
            {
                "v1": "prvName",
                "v2": "county",
                "v1_pos": 19
            },
            {
                "v1": "Facility_Division",
                "v2": "division",
                "v1_pos": 20
            },


        ],
        "file_name": "0016_facilities.json",
        "folder": "demo",
        "model_name": "facilities.Facility",
        "unique_fields": ["code"],
        "data": [],
        "database": "mssql+pyodbc://mfl:#Brian123@192.168.56.101:1433/tiba_live?driver=freetds", # NOQA
        "sql": ("SELECT Facility_Code, Facility_Name, Facility_Official_Name, LOWER(LTRIM(RTRIM(Facility_Nearest_Town))), LOWER(LTRIM(RTRIM(Facility_Plot_Number))), Location_Description, Open24Hours, OpenWeekends, CONVERT(VARCHAR, Date_Added, 126), Date_Modified, Num_Beds, Num_Cots, typName, ownName, kphName, regName, staDisplayName,Facility_latitude, facility_longitude, prvName, Facility_Division from all_login_facilities_view;")  # NOQA
    }
    ]


def port_data():
    create_engine = CreateJsonFiles()
    print "Fetching data from mfl_v1"
    for resource in SETUP_DATA_CONFIG:
        resource_name = resource.get("resource_name")
        print "Fetching {}".format(resource_name)
        resource_db = resource.get('database', None)
        if not resource_db:
            database = sa.create_engine(DEFAULT_DB)
        else:
            database = sa.create_engine(resource_db)

        mfl_v1_object_name = resource.get("mfl_v1_object_name")
        file_name = resource.get("file_name")
        folder = resource.get("folder")
        model_name = resource.get("model_name")
        unique_fields = resource.get("unique_fields")
        data = resource.get("data", None)
        field_map = resource.get("mfl_v1_v2_fields_map")
        resource_sql = resource.get("sql", None)
        data_path = resource.get("data_file_path", None)

        if not len(data) and mfl_v1_object_name != "N/A":
            sql = "SELECT * from {}".format(mfl_v1_object_name)

            sql = sql if not resource_sql else resource_sql

            clean_data = []

            for obj in database.connect().execute(sql):

                row_data = {}
                for field in field_map:
                    # create new user passwords
                    if field.get('is_password'):
                        row_data['password'] = make_password(obj[field.get("v1_pos")])
                        print 'user pass'
                        continue
                    # creaate the user groups
                    if field.get('is_user_group'):
                        row_data['group'] = field['group_field_name']
                        row_data['user'] = obj[field.get("user_field_pos")]
                        print 'user group'
                        continue

                    if field.get('is_user_county'):
                        row_data['county'] = obj[field.get("county_name_pos")]
                        row_data['user'] = obj[field.get("user_field_pos")]
                        print 'user county'
                        continue
                    if field.get('is_user_phone'):
                        row_data['phone_number'] = obj[field.get("phone_no_pos")]
                        row_data['user'] = obj[field.get("user_field_pos")]
                        print 'user phone'
                        continue

                    if field.get('is_user_email'):
                        row_data['email'] = obj[field.get("emal_pos")]
                        row_data['user'] = obj[field.get("user_field_pos")]
                        print 'user email'
                        continue

                    # create the user contacts

                    if not field.get("fk_map"):
                        try:
                            if obj[field.get("v1_pos")] and isinstance(
                                    obj[field.get("v1_pos")], str):
                                value = obj[field.get("v1_pos")].decode('cp1251')
                            else:
                                value = obj[field.get("v1_pos")]
                        except:
                            
                            
                        if value:
                            row_data[field.get("v2")] = value
                    else:
                        fk = field.get("fk_map")[0]
                        if not field.get('v2_value'):
                            if obj[field.get("v1_pos")] and isinstance(
                                    obj[field.get("v1_pos")], str):
                                value = obj[field.get("v1_pos")].decode(
                                    'cp1251')
                            else:
                                value = obj[field.get("v1_pos")]
                            if value and value != "":
                                row_data[field.get("v2")] = {
                                    fk.get("field_name"): value
                                }
                        else:
                            row_data[field.get("v2")] = {
                                fk.get("field_name"): field.get("v2_value")
                            }

                clean_data.append(row_data)

            data = clean_data
        elif not len(data) and data_path:
            with open(data_path) as data_file:
                string_data = data_file.read()
                data = json.loads(string_data)[0].get("records")

        create_engine.create_single_json_file(
            file_name, folder, model_name, unique_fields,
            data
        )

        print "{} {} Fetched".format(len(data), resource_name)


# def get_geo_codes():
#     database = sa.create_engine(DEFAULT_DB)
#     sql = "SELECT "


# from data.db_views import __all__


# def setup_views():
#     database = sa.create_engine(DEFAULT_DB)

#     for view in __all__:
#         database.connect().execute(view)


from django.core.management import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        print "Setting up the database views"
        # setup_views()
        print "Finished setting up the database views"

        port_data()
