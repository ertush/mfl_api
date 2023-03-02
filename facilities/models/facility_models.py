from __future__ import division
# from facilities.models.infrastructure import FacilityInfrastructure

import reversion
import json
import logging
import re
import datetime

from dateutil import parser

from django.conf import settings
from django.core import validators
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.utils import encoding, timezone
from django.contrib.gis.geos import Point
from django.contrib.postgres.fields import ArrayField


from users.models import JobTitle  # NOQA
from search.search_utils import index_instance
from common.models import (
    AbstractBase, Ward, Contact, SequenceMixin, SubCounty, County,
    Town, ApiAuthentication
)
from common.fields import SequenceField
from django.contrib.sessions.backends.db import SessionStore
import threading, requests, base64

LOGGER = logging.getLogger(__name__)


@encoding.python_2_unicode_compatible
class DhisAuth(ApiAuthentication):
    '''
    Authenticates to DHIS via OAuth2.
    Handles All API related functions
    '''

    oauth2_token_variable_name = models.CharField(max_length=255, default="api_oauth2_token", null=False, blank=False)
    type = models.CharField(max_length=255, default="DHIS2")
    session_store = SessionStore(session_key="dhis2_api_12904rs")

    def set_interval(self, interval, times=-1):
        # This will be the actual decorator,
        # with fixed interval and times parameter
        def outer_wrap(function):
            # This will be the function to be
            # called
            def wrap(*args, **kwargs):
                stop = threading.Event()

                # This is another function to be executed
                # in a different thread to simulate setInterval
                def inner_wrap():
                    i = 0
                    while i != times and not stop.isSet():
                        stop.wait(interval)
                        function(*args, **kwargs)
                        i += 1

                t = threading.Timer(0, inner_wrap)
                t.daemon = True
                t.start()
                return stop

            return wrap

        return outer_wrap

    @set_interval(30.0, -1)
    def refresh_oauth2_token(self):
        r = requests.post(
            settings.DHIS_ENDPOINT+"uaa/oauth/token",
            headers={
                "Authorization": "Basic " + base64.b64encode(settings.DHIS_CLIENT_ID + ":" + settings.DHIS_CLIENT_SECRET),
                "Accept": "application/json"
            },
            params={
                "grant_type": "refresh_token",
                "refresh_token": json.loads(self.session_store[self.oauth2_token_variable_name].replace("u", "")
                    .replace("'", '"'))["refresh_token"]
            }
        )

        response = str(r.json())
        # print("Response @ refresh_oauth2 ", response)
        self.session_store[self.oauth2_token_variable_name] = response
        self.session_store.save()

    def get_oauth2_token(self):
        r = requests.post(
            settings.DHIS_ENDPOINT+"uaa/oauth/token",
            headers={
                "Authorization": "Basic "+base64.b64encode(settings.DHIS_CLIENT_ID+":"+settings.DHIS_CLIENT_SECRET),
                "Accept": "application/json"
            },
            params={
                "grant_type": "password",
                "username": settings.DHIS_USERNAME,
                "password": settings.DHIS_PASSWORD
            }
        )

        response = str(r.json())
        # print("Response @ get_oauth2 ", response)
        self.session_store[self.oauth2_token_variable_name] = response
        self.session_store.save()
        self.refresh_oauth2_token()

    def generate_uuid_dhis(self):
        r_generate_orgunit_uid = requests.get(
            settings.DHIS_ENDPOINT + "api/system/uid.json",
            auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
            headers={
                # "Authorization": "Bearer " + json.loads(self.session_store[self.oauth2_token_variable_name].replace("u", "")
                #                                         .replace("'", '"'))["access_token"],
                "Accept": "application/json"
            },
        )
        print("New OrgUnit UID Generated-", r_generate_orgunit_uid.json()['codes'][0])
        return r_generate_orgunit_uid.json()['code'][0]

    def get_org_unit_id(self, code):
        r = requests.get(
            settings.DHIS_ENDPOINT + "api/organisationUnits.json",
            auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
            headers={
                "Accept": "application/json"
            },
            params={
                "filter": "code:eq:"+str(code),
                "fields": "[id]",
                "paging": "false"
            }
        )
        print("Get Org Unit ID Response", r.text, str(code))
        if len(r.json()["organisationUnits"]) is 1:
            # raise ValidationError(
            #     {
            #         "Error!": ["This facility is already available in DHIS2. Please ensure details are correct"]
            #     }
            # )
            return [r.json()["organisationUnits"][0]["id"], 'retrieved']
        else:
            r_generate_orgunit_uid = requests.get(
                settings.DHIS_ENDPOINT + "api/system/uid.json",
                auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
                headers={
                    "Accept": "application/json"
                },
            )
            # print("New OrgUnit UID Generated-", r_generate_orgunit_uid.json()['codes'][0])
            return [r_generate_orgunit_uid.json()['codes'][0], 'generated']
            # raise ValidationError(
            #     {
            #         "Error!": ["Unable to resolve exact organisation unit of the facility to be updated in DHIS2. "
            #                    "Most probably, the corresponding MFL code for the facility does not exist in DHIS2"]
            #     }
            # )

    def get_parent_id(self, ward_id):
        print (self.session_store[self.oauth2_token_variable_name])
        r = requests.get(
            settings.DHIS_ENDPOINT+"api/organisationUnits.json",
            auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
            headers={
                "Accept": "application/json"
            },
            params={
                "query": "KE_Ward_" + str(ward_id),
                "fields": "[id,name]",
                "filter": "level:in:[4]",
                "paging": "false"
            }
        )
        dhis2_facility = r.json()["organisationUnits"]

        if len(dhis2_facility) == 0:
            raise ValidationError(
                {
                    "Error!": ["Unable to resolve exact parent of the new facility in DHIS2"]
                }
            )
        else:
            return dhis2_facility[0]["id"]

    def push_facility_to_dhis2(self, new_facility_payload, new_facility=True):
        if new_facility:
            r = requests.post(
                settings.DHIS_ENDPOINT+"api/organisationUnits",
                auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
                headers={
                    # "Authorization": "Bearer " + json.loads(self.session_store[self.oauth2_token_variable_name].replace("u", "")
                    #                                         .replace("'", '"'))["access_token"],
                    "Accept": "application/json"
                },
                json=new_facility_payload
            )
            LOGGER.info("Create Facility Response: %s" % r.text)
        else:
            r = requests.put(
                settings.DHIS_ENDPOINT + "api/organisationUnits/" + new_facility_payload.pop('id'),
                auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
                headers={
                    "Accept": "application/json"
                },
                json=new_facility_payload
            )
            LOGGER.info("Update Facility Response: %s" % r.text)
        if r.json()["status"] != "OK":
            LOGGER.error('Facility feedback: %s' % r.text)
            raise ValidationError(
                {
                    "Error!": ["An error occured while pushing facility to DHIS2. This is may be caused by the "
                               "existance of an organisation unit with as similar name as to the one you are creating. "
                               "Or some specific information like codes are not unique"]
                }
            )

    def push_facility_metadata(self, metadata_payload, facility_uid):
        # Keph Level
        r_keph = requests.post(
            settings.DHIS_ENDPOINT + "api/organisationUnitGroups/" + metadata_payload['keph'] + "/organisationUnits/" + facility_uid,
            auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
            headers={
                "Accept": "application/json"
            },
        )
        # print r_keph.json()
        # if r_keph.json()["status"] != "OK":
        #     raise ValidationError(
        #         {
        #             "Error!": ["An error occured with allocation of KEPH level to DHIS"]
        #         }
        #     )
        r_facility_type = requests.post(
            settings.DHIS_ENDPOINT + "api/organisationUnitGroups/" + metadata_payload['facility_type'] + "/organisationUnits/" + facility_uid,
            auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
            headers={
                "Accept": "application/json"
            },
        )
        # if r_facility_type.json()["status"] != "OK":
        #     raise ValidationError(
        #         {
        #             "Error!": ["An error occured witha allocation of facility type to DHIS2"]
        #         }
        #     )
        r_ownership = requests.post(
            settings.DHIS_ENDPOINT + "api/organisationUnitGroups/" + metadata_payload[
                'ownership'] + "/organisationUnits/" + facility_uid,
            auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
            headers={
                "Accept": "application/json"
            },
        )
        # if r_ownership.json()["status"] != "OK":
        #     raise ValidationError(
        #         {
        #             "Error!": ["An error occured witha allocation of Ffacility ownership to DHIS2"]
        #         }
        #     )

    def push_facility_updates_to_dhis2(self, org_unit_id, facility_updates_payload):
        r = requests.put(
            settings.DHIS_ENDPOINT + "api/organisationUnits/"+org_unit_id,
            auth=(settings.DHIS_USERNAME, settings.DHIS_PASSWORD),
            headers={
                "Accept": "application/json"
            },
            json=facility_updates_payload
        )

        print("Update Facility Response", r.url, r.status_code, r.json())

        if r.json()["status"] != "OK":
            raise ValidationError(
                {
                    "Error!": ["Unable to push facility updates to DHIS2"]
                }
            )

    def format_coordinates(self, str_coordinates):
        coordinates_str_list = str_coordinates.split(" ")
        return str([float(coordinates_str_list[0]), float(coordinates_str_list[1])])

    def __str__(self):
        return "{}: {}".format("Dhis Auth - ", settings.DHIS_USERNAME)



class FacilityKephManager(models.Manager):

    def get_queryset(self):
        return super(
            FacilityKephManager, self).get_queryset().filter(
            is_facility_level=True)


@reversion.register
@encoding.python_2_unicode_compatible
class KephLevel(AbstractBase):

    """
    Hold the classification of facilities according to
    Kenya Essential Package for health (KEPH)

    Currently there are level 1 to level 6
    """
    name = models.CharField(
        max_length=30, help_text="The name of the KEPH e.g Level 1")
    description = models.TextField(
        null=True, blank=True,
        help_text='A short description of the KEPH level')
    is_facility_level = models.BooleanField(
        default=True, help_text='Is the KEPH level applicable to facilities')

    objects = FacilityKephManager()
    everything = models.Manager()

    def __str__(self):
        return self.name


@reversion.register
@encoding.python_2_unicode_compatible
class OwnerType(AbstractBase):

    """
    Sub divisions of owners of facilities.

    Owners of facilities could be classified into several categories.
    E.g we could have government, corporate owners, faith based owners
    private owners.
    """
    name = models.CharField(
        max_length=100,
        help_text="Short unique name for a particular type of owners. "
        "e.g INDIVIDUAL")
    abbreviation = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(
        null=True, blank=True,
        help_text="A brief summary of the particular type of owner.")

    def __str__(self):
        return self.name


@reversion.register(follow=['owner_type'])
@encoding.python_2_unicode_compatible
class Owner(AbstractBase, SequenceMixin):

    """
    Entity that has exclusive legal rights to the facility.

    For the master facility list, ownership especially for the faith-based
    facilities is broadened to also include the body that coordinates
    service delivery and health programs. Therefore, the Christian Health
    Association of Kenya (CHAK), Kenya Episcopal Conference (KEC), or
    Supreme Council of Kenya Muslim (SUPKEM) will be termed as owners though
    in fact the facilities under them are owned by the individual churches,
    mosques, or communities affiliated with the faith.
    """
    name = models.CharField(
        max_length=100, unique=True,
        help_text="The name of owner e.g Ministry of Health.")
    description = models.TextField(
        null=True, blank=True, help_text="A brief summary of the owner.")
    code = SequenceField(
        unique=True,
        help_text="A unique number to identify the owner."
        "Could be up to 7 characters long.", editable=False)
    abbreviation = models.CharField(
        max_length=30, null=True, blank=True,
        help_text="Short form of the name of the owner e.g Ministry of health"
        " could be shortened as MOH")
    owner_type = models.ForeignKey(
        OwnerType,
        help_text="The classification of the owner e.g INDIVIDUAL",
        on_delete=models.PROTECT)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_next_code_sequence()
        super(Owner, self).save(*args, **kwargs)

    def __str__(self):
        return self.name


@reversion.register(follow=['officer', 'contact'])
@encoding.python_2_unicode_compatible
class OfficerContact(AbstractBase):

    """
    The contact details of the officer in-charge.

    The officer in-charge may have as many mobile numbers as possible.
    Also the number of email addresses is not limited.
    """
    officer = models.ForeignKey(
        'Officer',
        help_text="The is the officer in charge", on_delete=models.PROTECT,
        related_name='officer_contacts')
    contact = models.ForeignKey(
        Contact,
        help_text="The contact of the officer in-charge may it be email, "
        " mobile number etc", on_delete=models.PROTECT)

    def __str__(self):
        return "{}: ({})".format(self.officer, self.contact)


@reversion.register(follow=['job_title', 'contacts'])
@encoding.python_2_unicode_compatible
class Officer(AbstractBase):

    """
    Identify officers in-charge of facilities

    In order to indicate whether an officer(practitioner) has a case or not
    The active field will be used.
    If the officer has case the active field will be set to false
    """
    name = models.CharField(
        max_length=255,
        help_text="the name of the officer in-charge e.g Roselyne Wiyanga ")
    id_number = models.CharField(
        max_length=10, null=True, blank=True,
        help_text='The  National Identity number of the officer')
    registration_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="This is the license number of the officer. e.g for a nurse"
        " use the NCK registration number.")
    job_title = models.ForeignKey('users.JobTitle', on_delete=models.PROTECT)

    contacts = models.ManyToManyField(
        Contact, through=OfficerContact,
        help_text='Personal contacts of the officer in charge')

    def get_officer_contacts(self):
        return [
            {
                "contact": contact.contact.contact,
                "contact_type": contact.contact.contact_type.name
            } for contact in self.officer_contacts.all()]

    def get_contact_by_type(self, contact_type_name):
        contacts =  self.get_officer_contacts()
        cons = [
            contact.get('contact') for contact in contacts
            if contact.get('contact_type') == contact_type_name
        ]
        return ', '.join(cons)

    def email(self):
        return self.get_contact_by_type('EMAIL')

    def postal(self):
        return self.get_contact_by_type('POSTAL')

    def mobile(self):
        return self.get_contact_by_type('MOBILE')

    def landline(self):
        return self.get_contact_by_type('LANDLINE')

    def fax(self):
        return self.get_contact_by_type('FAX')

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'officers in charge'


@reversion.register
@encoding.python_2_unicode_compatible
class FacilityStatus(AbstractBase):

    """
    Facility Operational Status covers the following elements:
    whether the facility
        1. has been approved to operate
        2. is operating
        3. is temporarily non-operational
        4. is closed down.
    """
    name = models.CharField(
        max_length=100, unique=True,
        help_text="A short name representing the operation status"
        " e.g OPERATIONAL")
    description = models.TextField(
        null=True, blank=True,
        help_text="A short explanation of what the status entails.")
    is_public_visible = models.BooleanField(
        default=False,
        help_text='The facilities with this status '
        'should be visible to the public')

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'facility statuses'


@reversion.register
@encoding.python_2_unicode_compatible
class FacilityAdmissionStatus(AbstractBase):

    """
    Facility Admission Status covers the following elements:
    whether the facility
        1. Not admitting
        2. Admitting general & maternity
        3. Admitting maternity only
    """
    name = models.CharField(
        max_length=100, unique=True,
        help_text="A short name representing the admission status"
        " e.g NOT ADMITTING")
    description = models.TextField(
        null=True, blank=True,
        help_text="A short explanation of what the admission status entails.")

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'facility admission statuses'


@reversion.register(follow=['preceding', ])
@encoding.python_2_unicode_compatible
class FacilityType(AbstractBase):
    owner_type = models.ForeignKey(
        OwnerType, null=True, blank=True)
    name = models.CharField(
        max_length=100, unique=True,
        help_text="A short unique name for the facility type e.g DISPENSARY")
    abbreviation = models.CharField(
        max_length=100, null=True, blank=True)
    sub_division = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="Parent of the facility type e.g sub-district hospitals "
        "are under Hospitals.")
    preceding = models.ForeignKey(
        'self', null=True, blank=True, related_name='preceding_type',
        help_text='The facility type that comes before this type')
    parent = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True)

    def __str__(self):
        return self.name

    def validate_sub_division(self):
        if self.sub_division:
            parent_type = self.__class__.objects.get(name=self.sub_division)
            self.parent = parent_type
        else:
            self.parent = None

    def clean(self, *args, **kwargs):
        super(FacilityType, self).clean(*args, **kwargs)
        self.validate_sub_division()

    class Meta(AbstractBase.Meta):
        unique_together = ('name', )


@reversion.register(follow=['regulating_body', 'contact'])
@encoding.python_2_unicode_compatible
class RegulatingBodyContact(AbstractBase):

    """
    A regulating body contacts.
    """
    regulating_body = models.ForeignKey(
        'RegulatingBody', related_name='reg_contacts', on_delete=models.PROTECT,)
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT,)

    def __str__(self):
        return "{}: ({})".format(self.regulating_body, self.contact)


@reversion.register(follow=['regulatory_body_type', 'default_status'])  # noqa
@encoding.python_2_unicode_compatible
class RegulatingBody(AbstractBase):

    """
    Bodies responsible for licensing of facilities.

    This is normally based on the relationship between the facility
    owner and the Regulator. For example, MOH-owned facilities are
    gazetted by the Director of Medical Services (DMS)  and the facilities
    owned by private practice nurses are licensed by the NCK.
    In some cases this may not hold e.g a KMPDB and not NCK will license a
    nursing home owned by a nurse
    """
    name = models.CharField(
        max_length=100, unique=True,
        help_text="The name of the regulating body")
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="A short-form of the name of the regulating body e.g Nursing"
        "Council of Kenya could be abbreviated as NCK.")
    regulation_verb = models.CharField(
        max_length=100, null=True, blank=True)
    regulatory_body_type = models.ForeignKey(
        OwnerType, null=True, blank=True,
        help_text='Show the kind of institutions that the body regulates e.g'
        'private facilities')
    default_status = models.ForeignKey(
        "RegulationStatus", null=True, blank=True,
        help_text="The default status for the facilities regulated by "
        "the particular regulator")

    @property
    def postal_address(self):
        contacts = RegulatingBodyContact.objects.filter(
            regulating_body=self,
            contact__contact_type__name='POSTAL')
        return contacts[0]

    @property
    def contacts(self):
        return [
            {
                "id": con.id,
                "contact": con.contact.contact,
                "contact_id": con.contact.id,
                "contact_type": con.contact.contact_type.id
            }
            for con in RegulatingBodyContact.objects.filter(
                regulating_body=self)
        ]

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'regulating bodies'


@reversion.register(follow=['regulatory_body', 'user'])
@encoding.python_2_unicode_compatible
class RegulatoryBodyUser(AbstractBase):

    """
    Links user to a regulatory body.
    These are the users who  will be carrying out the regulatory activities
    """
    regulatory_body = models.ForeignKey(
        RegulatingBody, on_delete=models.PROTECT,)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name='regulatory_users',
        on_delete=models.PROTECT,)

    def _ensure_a_user_is_linked_to_just_one_regulator(self):
        reg_user_records = self.__class__.objects.filter(
            regulatory_body=self.regulatory_body,
            user=self.user, active=True).count()
        if reg_user_records > 0:
            raise ValidationError(
                {
                    "user": [
                        "The user {0} is already linked to the selected "
                        "regulator {1}".format(
                            self.user.get_full_name,
                            self.regulatory_body.name)]
                }
            )
        else:
            msg = "The user {0} was successfully linked to the regulator {1}"\
                "".format(self.user.id, self.regulatory_body.id)
            LOGGER.info(msg)

    def make_user_national_user(self):
        self.user.is_national = True
        self.user.save()

    def __str__(self):
        return "{}: {}".format(self.regulatory_body, self.user)

    def clean(self, *args, **kwargs):
        self._ensure_a_user_is_linked_to_just_one_regulator()
        self.make_user_national_user()


@reversion.register(follow=['previous_status', 'next_status', ])
@encoding.python_2_unicode_compatible
class RegulationStatus(AbstractBase):

    """
    A Regulation state.

    The regulation states could be
        1. Pending Licensing: A facility that has been recommended by the DHMT
            but is  waiting for the license from the National Regulatory Body.

        2: Licensed:
            A facility that has been approved and issued a license by the
            appropriate National Regulatory Body.
        3. License Suspended:
            A facility whose license has been temporarily stopped for
            reasons including self-request, sickness, and disciplinary action.
        4. License Canceled:
            A facility whose license has been permanently stopped by the
            national body.
        5. Pending Registration:
            A facility that has been approved by the DHMT as an Institution
            and a request for registration sent the KMPDB.
        6. Registered:
            A facility that has been approved as an institution by
            the KMPDB and a registration number given.
        7. Pending Gazettement:
            A facility that has been inspected and recommended by the DHMT
            (or District Development Committee [DDC] or presidential mandate)
            for gazettement as a MOH facility, but has not yet been officially
            gazetted. The facility is awaiting official gazettement and is
            known as 'pending gazettement'.
        8. Gazetted:
            A facility that has been gazetted and the notice published in the
            Kenya Gazette.

    There are number of fields that are worth looking at:
        is_initial_state:
            This is the state that shows whether the state is the
            first state
            Is should be only one for the entire API
        is_final_state:
            This is last state of the of the workflow state.
            Just like the is_initial_state is should be the only one in the
            entire workflow
        previous_status:
            If status has a a preceding status, it should added here.
            If does not then leave it blank.
            A status can have only one previous state.
        next_status:
            If the status has a succeeding status, it should be added here,
            If does not not leave it blank
            Again just the 'previous' field,  a status can have only one
            'next' field.
    """
    name = models.CharField(
        max_length=100, unique=True,
        help_text="A short unique name representing a state/stage of "
        "regulation e.g. PENDING_OPENING ")
    description = models.TextField(
        null=True, blank=True,
        help_text="A short description of the regulation state or state e.g"
        "PENDING_LICENSING could be described as 'waiting for the license to"
        "begin operating' ")
    previous_status = models.ForeignKey(
        'self', related_name='previous_state', null=True, blank=True,
        help_text='The regulation_status preceding this regulation status.')
    next_status = models.ForeignKey(
        'self', related_name='next_state', null=True, blank=True,
        help_text='The regulation_status succeeding this regulation status.')
    is_initial_state = models.BooleanField(
        default=False,
        help_text='Indicates whether it is the very first state'
        'in the regulation workflow.')
    is_final_state = models.BooleanField(
        default=False,
        help_text='Indicates whether it is the last state'
        ' in the regulation work-flow')
    is_default = models.BooleanField(
        default=False,
        help_text='The default regulation status for facilities')

    @property
    def previous_state_name(self):
        if self.previous_status:
            return self.previous_status.name
        else:
            return ""

    @property
    def next_state_name(self):
        if self.next_status:
            return self.next_status.name
        else:
            return ""

    def validate_only_one_final_state(self):
        final_state = self.__class__.objects.filter(
            is_final_state=True)
        if final_state.count() > 0 and self.is_final_state:
            raise ValidationError("Only one final state is allowed.")

    def validate_only_one_initial_state(self):
        initial_state = self.__class__.objects.filter(is_initial_state=True)
        if initial_state.count() > 0 and self.is_initial_state:
            raise ValidationError("Only one Initial state is allowed.")

    def validate_only_one_default_status(self):
        default_states_count = self.__class__.objects.filter(
            is_default=True).count()
        if self.is_default and default_states_count >= 1:
            raise ValidationError(
                "Only one default regulation status is allowed")

    def clean(self, *args, **kwargs):
        self.validate_only_one_final_state()
        self.validate_only_one_initial_state()
        self.validate_only_one_default_status()
        super(RegulationStatus, self).clean(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'regulation_statuses'


@reversion.register(follow=['regulating_body', 'regulation_status'])
@encoding.python_2_unicode_compatible
class FacilityRegulationStatus(AbstractBase):

    """
    Shows the regulation status of a facility.

    It adds the extra reason field that makes it possible to give
    an explanation as to why a facility is in a certain regulation status.
    """
    facility = models.ForeignKey(
        'Facility', on_delete=models.PROTECT,
        related_name='regulatory_details')
    regulating_body = models.ForeignKey(
        RegulatingBody, on_delete=models.PROTECT, null=True, blank=True)
    regulation_status = models.ForeignKey(
        RegulationStatus, on_delete=models.PROTECT)
    reason = models.TextField(
        null=True, blank=True,
        help_text="An explanation for as to why is the facility is being"
        "put in the particular status")
    license_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='The license number that the facility has been '
        'given by the regulator')
    license_is_expired = models.BooleanField(
        default=False,
        help_text='A flag to indicate whether the license is valid or not')

    def __str__(self):
        return "{}: {}".format(self.facility, self.regulation_status.name)

    # def clean(self, *args, **kwargs):
    #     self.facility.regulated = True
    #     self.facility.license_number = self.license_number
    #     self.facility.save(allow_save=True)

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'facility regulation statuses'

    def save(self, *args, **kwargs):

        if not self.regulating_body and self.facility.regulatory_body:
            self.regulating_body = self.facility.regulatory_body

        if not self.regulating_body and  self.created_by.regulator:
            self.regulating_body =  self.created_by.regulatory

        super(FacilityRegulationStatus, self).save(*args, **kwargs)


@reversion.register(follow=['facility', 'contact'])
@encoding.python_2_unicode_compatible
class FacilityContact(AbstractBase):

    """
    The facility contact.

    The facility contacts could be as many as the facility has.
    They also could be of as many different types as the facility has;
    they could be emails, phone numbers, land lines etc.
    """
    facility = models.ForeignKey(
        'Facility', related_name='facility_contacts', on_delete=models.PROTECT)
    contact = models.ForeignKey(Contact, on_delete=models.PROTECT)

    def __str__(self):
        return "{}: ({})".format(self.facility, self.contact)

    class Meta(AbstractBase.Meta):
        unique_together = ('facility', 'contact')


class FacilityExportExcelMaterialView(models.Model):

    """
    Django's Interface to the facility material view.

    This speeds up fetching facilities
    """

    id = models.UUIDField(primary_key=True)
    name = models.CharField(
        max_length=100, help_text='Unique name of the facility')
    officialname = models.CharField(
        max_length=100, help_text='Official name of the facility')
    code = models.IntegerField(help_text='The facility code')
    registration_number = models.CharField(
        max_length=100,
        help_text='The facilities registration_number')
    keph_level_name = models.UUIDField(
        null=True, blank=True,
        help_text='The facility\'s keph-level')
    facility_type_name = models.CharField(
        max_length=100,
        help_text='The facility type')
    facility_type_category = models.CharField(
        max_length=100,
        help_text='The facility category name')
    facility_type_parent = models.UUIDField(null=True, blank=True,
                           help_text='The name of the facility\'s type parent uid')
    county = models.UUIDField(
        null=True, blank=True,
        help_text='Name of the facility\'s county')
    constituency = models.UUIDField(
        null=True, blank=True,
        help_text='The name of the facility\'s constituency ')
    ward = models.UUIDField(
        max_length=100,
        help_text='Name of the facility\'s ward')
    owner_name = models.CharField(
        max_length=100,
        help_text='The facility\'s owner')
    owner_type_name = models.CharField(
        max_length=100,
        help_text='The facility\'s owner type name')
    regulatory_body_name = models.CharField(
        max_length=100,
        help_text='The name of the facility\'s regulator')
    beds = models.IntegerField(
        help_text='The number of beds in the facility')
    cots = models.IntegerField(
        help_text='The number of cots in the facility')
    search = models.CharField(
        max_length=255, null=True, blank=True,
        help_text='A dummy search field')
    county_name = models.CharField(max_length=100, null=True, blank=True)
    constituency_name = models.CharField(max_length=100, null=True, blank=True)
    sub_county = models.CharField(max_length=100, null=True, blank=True)
    sub_county_name = models.CharField(max_length=100, null=True, blank=True)
    ward_name = models.CharField(max_length=100, null=True, blank=True)
    keph_level = models.CharField(max_length=100, null=True, blank=True)
    facility_type = models.CharField(max_length=100, null=True, blank=True)
    owner_type = models.CharField(max_length=100, null=True, blank=True)
    owner = models.UUIDField(null=True, blank=True)
    operation_status = models.UUIDField(null=True, blank=True)
    operation_status_name = models.CharField(
        max_length=100, null=True, blank=True)
    admission_status_name = models.CharField(
        max_length=100, null=True, blank=True)
    open_whole_day = models.BooleanField(
        default=False,
        help_text="Does the facility operate 24 hours a day")
    open_public_holidays = models.BooleanField(
        default=False,
        help_text="Is the facility open on public holidays?")
    open_weekends = models.BooleanField(
        default=False,
        help_text="Is the facility_open during weekends?")
    open_late_night = models.BooleanField(
        default=False,
        help_text="Indicates if a facility is open late night e.g up-to 11 pm")
    services = ArrayField(
        models.UUIDField(null=True, blank=True), null=True, blank=True
    )
    categories = ArrayField(
        models.UUIDField(null=True, blank=True), null=True, blank=True
    )
    service_names = ArrayField(
        models.UUIDField(null=True, blank=True), null=True, blank=True
    )
    approved = models.BooleanField(default=False)
    is_public_visible = models.BooleanField(default=False)
    created = models.DateTimeField()
    updated = models.DateTimeField()
    closed = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    long = models.CharField(max_length=30, null=True, blank=True)
    lat = models.CharField(max_length=30, null=True, blank=True)
    approved_national_level = models.BooleanField(default=False)

    class Meta(object):
        managed = False
        ordering = ('-created', )
        db_table = 'facilities_excel_export'


@reversion.register(follow=[
    'facility_type', 'operation_status', 'ward', 'owner', 'contacts',
    'parent', 'regulatory_body', 'keph_level', 'sub_county', 'town'
])
@encoding.python_2_unicode_compatible
class Facility(SequenceMixin, AbstractBase):

    """
    A health institution in Kenya.

    The health institution considered as facilities include:
    Health Centers, Dispensaries, Hospitals etc.
    """
    name = models.CharField(
        max_length=100,
        help_text='This is the unique name of the facility', unique=True)
    official_name = models.CharField(
        max_length=150, null=True, blank=True,
        help_text='The official name of the facility')
    code = SequenceField(
        unique=True, editable=False,
        help_text='A sequential number allocated to each facility',
        null=True, blank=True)
    registration_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="The registration number given by the regulator")
    abbreviation = models.CharField(
        max_length=30, null=True, blank=True,
        help_text='A short name for the facility.')
    description = models.TextField(
        null=True, blank=True,
        help_text="A brief summary of the Facility")
    number_of_beds = models.PositiveIntegerField(
        default=0,
        help_text="The number of authorized inpatient beds"
        " that a facility has. e.g 0")
    number_of_cots = models.PositiveIntegerField(
        default=0,
        help_text="The number of authorized cots that a facility has e.g 0")
    number_of_emergency_casualty_beds = models.PositiveIntegerField(
        default=0,
        help_text="The number of emergency casualty beds "
        " that a facility has e.g 0")
    number_of_icu_beds = models.PositiveIntegerField(
        default=0,
        help_text="The number of Intensive Care Units (ICU) beds"
        " that a facility has e.g 0")
    number_of_hdu_beds = models.PositiveIntegerField(
        default=0,
        help_text="The number of High Dependency Units (HDU) beds"
        " that a facility has e.g 0")
    number_of_inpatient_beds = models.PositiveIntegerField(
        default=0,
        help_text="The number of General In-patient beds"
        " that a facility has e.g 0")
    # <Additions>
    number_of_maternity_beds = models.PositiveIntegerField(
        default=0,
        help_text="The number of maternity beds"
        " that a facility has e.g 0")
    number_of_isolation_beds = models.PositiveIntegerField(
        default=0,
        help_text="The number of isolation beds"
        " that a facility has e.g 0")
    # </Additions>
    number_of_general_theatres = models.PositiveIntegerField(
        default=0,
        help_text="The number of general theatres "
        " that a facility has e.g 0")  
    number_of_maternity_theatres = models.PositiveIntegerField(
        default=0,
        help_text="The number of maternity theatres "
        " that a facility has e.g 0")  
    open_whole_day = models.BooleanField(
        default=False,
        help_text="Does the facility operate 24 hours a day")
    open_public_holidays = models.BooleanField(
        default=False,
        help_text="Is the facility open on public holidays?")
    open_normal_day = models.BooleanField(
        default=True,
        help_text="Is the facility open from 8 am to 5 pm")
    open_weekends = models.BooleanField(
        default=False,
        help_text="Is the facility_open during weekends?")
    open_late_night = models.BooleanField(
        default=False,
        help_text="Indicates if a facility is open late night e.g upto 11 pm")
    is_classified = models.BooleanField(
        default=False,
        help_text="Should the facility geo-codes be visible to the public?"
        "Certain facilities are kept 'off-the-map'")
    is_published = models.BooleanField(
        default=False,
        help_text="COnfirmation by the CHRIO that the facility is okay")
    facility_type = models.ForeignKey(
        FacilityType,
        help_text="This depends on who owns the facility. For MOH facilities,"
        "type is the gazetted classification of the facility."
        "For Non-MOH check under the respective owners.",
        on_delete=models.PROTECT)
    operation_status = models.ForeignKey(
        FacilityStatus, null=True, blank=True,
        on_delete=models.PROTECT,
        help_text="Indicates whether the facility"
        "has been approved to operate, is operating, is temporarily"
        "non-operational, or is closed down")
    accredited_lab_iso_15189 = models.BooleanField(
        default=False,
        help_text="Indicate if facility is accredited Lab ISO 15189")
    ward = models.ForeignKey(
        Ward, null=True, blank=True,
        on_delete=models.PROTECT,
        help_text="County ward in which the facility is located")

    county = models.ForeignKey(
        County, on_delete=models.PROTECT, null=True, blank=True)

    owner = models.ForeignKey(
        Owner, on_delete=models.PROTECT,
        help_text="A link to the organization that owns the facility")
    contacts = models.ManyToManyField(
        Contact, through=FacilityContact,
        help_text='Facility contacts - email, phone, fax, postal etc')
    parent = models.ForeignKey(
        'self', help_text='Indicates the umbrella facility of a facility',
        null=True, blank=True)
    attributes = models.TextField(null=True, blank=True)
    regulatory_body = models.ForeignKey(
        RegulatingBody, on_delete=models.PROTECT,
        null=True, blank=True,)
    keph_level = models.ForeignKey(
        KephLevel, null=True, blank=True,
        on_delete=models.PROTECT,
        help_text='The keph level of the facility')

    # set of boolean to optimize filtering though through tables
    regulated = models.BooleanField(default=False)
    approved =  models.NullBooleanField(
        blank=True, null=True, help_text='Has the facility been approved at the county level')
    rejected = models.BooleanField(default=False)
    has_edits = models.BooleanField(default=False)

    bank_name = models.CharField(
        max_length=100,
        null=True, blank=True,
        help_text="The name of the facility's banker e.g Equity Bank")
    branch_name = models.CharField(
        max_length=100,
        null=True, blank=True,
        help_text="Branch name of the facility's bank")
    bank_account = models.CharField(max_length=100, null=True, blank=True)
    facility_catchment_population = models.IntegerField(
        null=True, blank=True,
        help_text="The population size which the facility serves")
    sub_county = models.ForeignKey(
        SubCounty, null=True, blank=True,
        on_delete=models.PROTECT,
        help_text='The sub county in which the facility has been assigned')
    town = models.ForeignKey(
        Town, null=True, blank=True,
        on_delete=models.PROTECT,
        help_text="The town where the entity is located e.g Nakuru")
    town_name = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="The town where the entity is located e.g Nakuru")
    nearest_landmark = models.TextField(
        null=True, blank=True,
        help_text="well-known physical features /structure that can be used to"
        " simplify directions to a given place. e.g town market or village ")
    plot_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text="This is the same number found on the title deeds of the"
        "piece of land on which this facility is located")
    location_desc = models.TextField(
        null=True, blank=True,
        help_text="This field allows a more detailed description of "
        "the location")
    closed = models.BooleanField(
        default=False,
        help_text='Indicates whether a facility has been closed by'
        ' the regulator')
    closed_date = models.DateTimeField(
        null=True, blank=True, help_text='Date the facility was closed')
    closing_reason = models.TextField(
        null=True, blank=True, help_text="Reason for closing the facility")
    date_established = models.DateField(
        null=True, blank=True,
        help_text='The date when the facility became operational')
    license_number = models.CharField(
        max_length=100, null=True, blank=True,
        help_text='The license number given to the hospital by the regulator')
    regulation_status = models.ForeignKey(
        RegulationStatus, null=True, blank=True,
        on_delete=models.PROTECT,
        help_text='The regulatory status of the hospital')
    reporting_in_dhis = models.NullBooleanField(
        blank=True, null=True,
        help_text='A flag to indicate whether facility should have reporting in dhis')
    admitting_maternity_only = models.NullBooleanField(
        blank=True, null=True,
        help_text='A flag to indicate whether facility admits only maternity patients')
    admitting_maternity_general = models.NullBooleanField(
        blank=True, null=True,
        help_text='A flag to indicate whether facility admits both maternity & general casualty patients')
    admission_status = models.ForeignKey(
        FacilityAdmissionStatus, null=True, blank=True,
        on_delete=models.PROTECT,
        help_text="Indicates whether the facility"
        "has been approved to admit and the admission categories it caters for")
    reporting_in_dhis = models.NullBooleanField(
        blank=True, null=True,
        help_text='A flag to indicate whether facility should have reporting in dhis')
    nhif_accreditation = models.NullBooleanField(
        blank=True, null=True, default=False,
        help_text='A flag to indicate whether facility is accredited by nhif')
    approved_national_level = models.NullBooleanField(
        blank=True, null=True, help_text='Has the facility been approved at the national level')

    dhis2_api_auth = DhisAuth()

    def push_new_facility(self, code=None):
        if self.approved_national_level and str(self.operation_status.id) == 'ae75777e-5ce3-4ac9-a17e-63823c34b55e' \
                and self.reporting_in_dhis is True and settings.PUSH_TO_DHIS:
            from mfl_gis.models import FacilityCoordinates
            import re
            self.dhis2_api_auth.get_oauth2_token()

            dhis2_parent_id = self.dhis2_api_auth.get_parent_id(self.ward.code)
            dhis2_org_unit_id = self.dhis2_api_auth.get_org_unit_id(self.code)
            kmhfl_dhis2_facility_type_mapping = {
                "20b86171-0c16-47e1-9277-5e773d485c33": "YQK9pleIoeB",
                "5eb392ac-d10a-40c9-b525-53dac866ef6c": "lTrpyOiOcM6",
                "8949eeb0-40b1-43d4-a38d-5d4933dc209f": "lTrpyOiOcM6",
                "ccc1600e-9a24-499f-889f-bd9f0bdc4b95": "YQK9pleIoeB",
                "d8d741b1-21c5-45c8-86d0-a2094bf9bda6": "YQK9pleIoeB",
                "85f2099b-a2f8-49f4-9798-0cb48c0875ff": "YQK9pleIoeB",
                "869118aa-0e97-4f47-b6b7-1f295d109c8f": "YQK9pleIoeB",
                "a8af148f-b1b6-4eed-9d86-07d4f3135229": "YQK9pleIoeB",
                "74755372-99ba-4b70-bca8-a583f03990bc": "lTrpyOiOcM6",
                "4714529e-21de-4d5c-89da-11e335831327": "lTrpyOiOcM6",
                "52ccbc58-2a71-4a66-be40-3cd72e67f798": "CGDNIWGHRNr",
                "831a23c1-9124-4ce1-a0cf-60b59ef0fba5": "YQK9pleIoeB",
                "336bf913-b42e-476a-bf47-11d3f769922f": "YQK9pleIoeB",
                "f222bab7-589c-4ba8-bd9a-fe6c96fcd085": "CGDNIWGHRNr",
                "35376bf5-2e83-4f70-8c4d-a7b80f782eb1": "YQK9pleIoeB",
                "479a9a16-219f-48f6-818d-b2c06ada2332": "rhKJPLo27x7",
                "b9a51572-c931-4cc5-8e21-f17b22b0fd20": "CGDNIWGHRNr",
                "1571711c-4b80-493b-8109-faab2e4f43f0": "YQK9pleIoeB",
                "4d47a5dd-628a-4049-a240-3ab767415c49": "rhKJPLo27x7",
                "0fa47f39-d58e-4a16-845c-82818719188d": "CGDNIWGHRNr",
                "22c161ee-577f-41ef-bd4e-dd0a26327bbc": "YQK9pleIoeB",
                "cd841f88-198a-4d8a-869c-3ab4a7091c11": "YQK9pleIoeB",
                "188551b7-4f22-4fc4-b07b-f9c9aeeea872": "rhKJPLo27x7",
                "e5923a48-6b22-42c4-a4e6-6c5a5e8e0b0e": "YQK9pleIoeB",
                "55d65dd6-5351-4cf4-a6d9-e05ce6d343ab": "mVrepdLAqSD",
                "87626d3d-fd19-49d9-98da-daca4afe85bf": "mVrepdLAqSD",
                "79158397-0d87-4d0e-8694-ad680a907a79": "YQK9pleIoeB",
                "031293d9-fd8a-4682-a91e-a4390d57b0cf": "YQK9pleIoeB",
                "4369eec8-0416-4e16-b013-e635ce46a02f": "YQK9pleIoeB",
            }
            kmhfl_dhis2_ownership_mapping = {
                "d45541f8-3b3d-475b-94f4-17741d468135": "aRxa6o8GqZN",
                "afc4bcdb-fc22-4336-8958-d2df06fe90ad": "aRxa6o8GqZN",
                "56937bed-ea04-4306-bdf9-86668eb570c7": "aRxa6o8GqZN",
                "122f57a8-51ef-4a26-9024-4b34386485fd": "aRxa6o8GqZN",
                "abda166b-5c02-44c8-8058-5e4112ef9f95": "eT1vvFVhLHc",
                "cd04053e-a5eb-425b-b4d7-24746c311fa6": "eT1vvFVhLHc",
                "a3477ae7-ee1e-410e-83b1-64bf8b723d95": "aRxa6o8GqZN",
                "9bbcb2b4-f1d6-449b-a2cf-e92db2d861df": "aRxa6o8GqZN",
                "5363e7ac-2728-4099-9f5b-da14e2ee83d0": "aRxa6o8GqZN",
                "f918d78e-e09b-4e91-8a97-f6229a27346b": "aRxa6o8GqZN",
                "4a1c60b2-85b3-41b5-aed7-8448b863d566": "aRxa6o8GqZN",
                "ddebc398-fe10-44c2-b45a-1a35b357ae99": "AaAF5EmS1fk",
                "15aa5a44-0833-4e8f-83e6-916e5e5ab213": "eT1vvFVhLHc",
                "28d7a8e1-e15c-4326-ace1-b2c1b81af586": "None",
                "4560545a-67c7-4b2b-87be-b0babee4cb83": "AaAF5EmS1fk",
                "2c62704b-8072-470c-a7e6-259384f364f7": "eT1vvFVhLHc",
                "cfe25392-4f85-49ea-b180-35388f47ea9e": "eT1vvFVhLHc",
                "93c0fe24-3f12-4be2-b5ff-027e0bd02274": "AaAF5EmS1fk",
                "c3bab995-0c29-433c-b39c-6b86d6084f5f": "AaAF5EmS1fk",
                "6cb92834-107c-404a-91fa-cf60b1eb5333": "aRxa6o8GqZN",
                "2e651780-2ed4-4f8c-9061-6e5acf95d581": "AaAF5EmS1fk",
                "30af7e3f-cd52-4ca0-b5dc-d8b1040a9808": "AaAF5EmS1fk",
                "d64bbd8a-4013-463b-a238-c346cee66a92": "AaAF5EmS1fk",
            }
            kmhfl_dhis2_keph_mapping = {
                "ed23da85-4c92-45af-80fa-9b2123769f49": "FpY8vg4gh46",
                "7824068f-6533-4532-9775-f8ef200babd1": "d5QX71PY5t0",
                "c0bb24c2-1a96-47ce-b327-f855121f354f": "hBZ5DRto7iF",
                "174f7d48-3b57-4997-a743-888d97c5ec31": "wwiu1jyZOXO",
                "ceab4366-4538-4bcf-b7a7-a7e2ce3b50d5": "tvMxZ8aCVou"
            }
            if code:
                facility_code = str(code)
            else:
                facility_code = str(self.code)
            new_facility_payload = {
                "id": dhis2_org_unit_id[0],
                "code": facility_code,
                "name": str(self.name),
                "shortName": str(self.name[:49]),
                "displayName": str(self.official_name),
                "parent": {
                    "id": dhis2_parent_id
                },
                "openingDate": self.date_established.strftime("%Y-%m-%d"),
                "coordinates": self.dhis2_api_auth.format_coordinates(
                    re.search(r'\((.*?)\)', str(FacilityCoordinates.objects.values('coordinates')
                                                .get(facility_id=self.id)['coordinates'])).group(1))
            }
            metadata_payload = {
                "facility_type": kmhfl_dhis2_facility_type_mapping[str(self.facility_type_id)],
                "keph": kmhfl_dhis2_keph_mapping[str(self.keph_level_id)],
                "ownership": kmhfl_dhis2_ownership_mapping[str(self.owner_id)]
            }
            new_facility = True
            if dhis2_org_unit_id[1] == 'retrieved':
                new_facility = False
            self.dhis2_api_auth.push_facility_to_dhis2(new_facility_payload, new_facility)
            # facility_uid = self.dhis2_api_auth.get_org_unit_id(self.code)
            facility_uid = dhis2_org_unit_id[0]
            self.dhis2_api_auth.push_facility_metadata(metadata_payload, facility_uid)
        else:
            pass

    def push_facility_updates(self):
        pass
        # if self.approved_national_level:
        #     from mfl_gis.models import FacilityCoordinates
        #     import re
        #     self.dhis2_api_auth.get_oauth2_token()
        #
        #     dhis2_parent_id = self.dhis2_api_auth.get_parent_id(self.ward.code)
        #     dhis2_org_unit_id = self.dhis2_api_auth.get_org_unit_id(self.code)
        #     new_facility_updates_payload = {
        #         "code": str(self.code),
        #         "name": str(self.name),
        #         "shortName": str(self.name),
        #         "displayName": str(self.official_name),
        #         "parent": {
        #             "id": dhis2_parent_id
        #         },
        #         "openingDate": self.facility.date_established.strftime("%Y-%m-%d"),
        #         "coordinates": self.dhis2_api_auth.format_coordinates(
        #             re.search(r'\((.*?)\)', str(FacilityCoordinates.objects.values('coordinates')
        #                                         .get(facility_id=self.id)['coordinates'])).group(1))
        #     }
        #
        #     self.dhis2_api_auth.push_facility_updates_to_dhis2(dhis2_org_unit_id, new_facility_updates_payload)

    def validate_facility_name(self):
        if self.pk:
            if self.__class__.objects.filter(name=self.name).count() != 1:
                raise ValidationError({"name": "The name must be unique"})
        else:
            if self.__class__.objects.filter(name=self.name).count() > 0:
                raise ValidationError({"name": "The name must be unique"})

    @property
    def in_complete_details(self):
        """
        Check whether  a facility has all the details filled in:
            1. Coordinates
            2. Contacts and officers
            3. Services

        This will be used to determine if the facility should have an MFL Code.
        The incomplete facilities should not have MFL codes
        """
        in_complete_data = []
        if not self.coordinates:
            in_complete_data.append('coordinates')

        if len(self.facility_contacts.all()) == 0:
            in_complete_data.append('contacts')

        if len(self.facility_services.all()) == 0:
            in_complete_data.append('services')

        if len(self.facility_infrastructure.all()) == 0:
            in_complete_data.append('infrastructure')


        if len(self.facility_specialists.all()) == 0:
            in_complete_data.append('humanresources')

        return ", ".join(in_complete_data)

    @property
    def is_complete(self):
        return self.in_complete_details == ""

    @property
    def facility_checklist_document(self):
        from common.models.model_declarations import DocumentUpload
        try:
            document = DocumentUpload.objects.get(
                facility_name=self.name, document_type="Facility_ChecKList")
            return {
                "id": document.id,
                "url": document.fyl.name,
            }
        except DocumentUpload.DoesNotExist:
            return None

    @property
    def facility_license_document(self):
        from common.models.model_declarations import DocumentUpload
        try:
            document = DocumentUpload.objects.get(
                facility_name=self.name, document_type="FACILITY_LICENSE")
            return {
                "id": document.id,
                "url": document.fyl.name,
            }
        except DocumentUpload.DoesNotExist:
            return None

    def update_facility_regulation_status(self):
        self.regulated = True
        if self.regulation_status:
            FacilityRegulationStatus.objects.create(
                license_number=self.license_number,
                regulation_status=self.regulation_status,
                regulating_body=self.regulatory_body,
                created_by=self.created_by,
                updated_by=self.updated_by,
                facility=self)

    # hard code the operational status name in order to avoid more crud
    @property
    def service_catalogue_active(self):
        if self.operation_status.name.lower() == "operational":
            return True
        else:
            return False

    @property
    def boundaries(self):
        from mfl_gis.models import (
            CountyBoundary, ConstituencyBoundary, WardBoundary)

        return {
            "county_boundary": str(CountyBoundary.objects.get(
                area=self.ward.constituency.county).id),
            "constituency_boundary": str(ConstituencyBoundary.objects.get(
                area=self.ward.constituency).id),
            "ward_boundary": str(WardBoundary.objects.get(area=self.ward).id)
        }

    @property
    def latest_update(self):
        facility_updates = FacilityUpdates.objects.filter(
            facility=self, approved=False, cancelled=False)
        if facility_updates:
            return str(facility_updates[0].id)
        else:
            return None

    @property
    def ward_name(self):
        return self.ward.name

    @property
    def get_county(self):
        return self.ward.constituency.county.name

    @property
    def get_constituency(self):
        return self.ward.constituency.name

    @property
    def current_regulatory_status(self):
        try:
            # returns in reverse chronological order so just pick the first one
            return self.regulatory_details.filter(
                facility=self)[0].regulation_status.name
        except IndexError:
            return self.regulatory_body.default_status.name

    @property
    def is_regulated(self):
        return (
            self.current_regulatory_status !=
            self.regulatory_body.default_status.name
        )

    @property
    def _county(self):
        return self.ward.constituency.county.name

    @property
    def constituency(self):
        return self.ward.constituency.name

    @property
    def operation_status_name(self):
        return self.operation_status.name
    
    @property
    def admission_status_name(self):
        return self.admission_status.name

    @property
    def facility_type_name(self):
        return self.facility_type.name

    @property
    def owner_name(self):
        return self.owner.name

    @property
    def owner_type_name(self):
        return self.owner.owner_type.name

    @property
    def is_approved(self):
        approvals = FacilityApproval.objects.filter(
            facility=self, is_cancelled=False).count()
        if approvals:
            return True
        else:
            False

    @property
    def latest_approval(self):
        approvals = FacilityApproval.objects.filter(
            facility=self, is_cancelled=False)

        if approvals:
            return approvals[0]
        else:
            return None

    @property
    def latest_approval_or_rejection(self):
        approvals = FacilityApproval.objects.filter(facility=self)
        if approvals:
            return {
                "id": str(approvals[0].id),
                "comment": str(approvals[0].comment)
            }
        else:
            return None

    @property
    def get_facility_services(self):
        """Digests the facility_services for the sake of frontend."""
        services = self.facility_services.all()

        return [
            {
                "id": service.id,
                "service_id": service.service.id,
                "service_name": str(service.service.name),
                "service_code": service.service.code,
                "option_name": str(
                    service.option.display_text) if service.option else "Yes",
                "option": str(
                    service.option.id) if service.option else None,
                "category_name": str(
                    service.service.category.name),
                "category_id": service.service.category.id,
                "average_rating": service.average_rating,
                "number_of_ratings": service.number_of_ratings
            }
            for service in services
        ]

    @property
    def get_facility_contacts(self):
        """For the same purpose as the get_facility_services above"""
      
        contacts = self.facility_contacts.all()

        return [
            {
                "id": contact.id,
                "contact_id": contact.contact.id,
                "contact": contact.contact.contact,
                "contact_type_name": contact.contact.contact_type.name
            }
            for contact in contacts
        ]

    @property
    def get_facility_infrastructure(self):
        """For the same purpose as the get_facility_contacts above"""
        infra = self.facility_infrastructure.all()

        return [
            {
                "id": inf.id,
                "name": inf.infrastructure.name,
                "count":inf.count,
                "infrastructure_category": inf.infrastructure.category.id,
                "infrastructure_category_name": str(inf.infrastructure.category.name),
            }
            for inf in infra
        ]

    @property
    def get_facility_specialities(self):
        """For the same purpose as the get_facility_infra... above"""
        hr = self.facility_specialists.all()

        return [
            {
                "id": h_r.id,
                "name": h_r.speciality.name,
                "count": h_r.count,
                "speciality_category": h_r.speciality.category.id,
                "speciality_category_name": str(h_r.speciality.category.name),
            }
            for h_r in hr
        ]


    @property
    def average_rating(self):
        avg_service_rating = [
            i.average_rating for i in self.facility_services.all()
        ]
        try:
            return sum(avg_service_rating, 0) / self.facility_services.count()
        except ZeroDivisionError:
            return 0

    @property
    def officer_in_charge(self):
        officer = FacilityOfficer.objects.filter(active=True, facility=self)
        if officer:
            officer_contacts = OfficerContact.objects.filter(
                officer=officer[0].officer)
            contacts = []
            for contact in officer_contacts:
                contacts.append({
                    "officer_contact_id": contact.id,
                    "type": contact.contact.contact_type.id,
                    "contact_type_name": contact.contact.contact_type.name,
                    "contact": contact.contact.contact,
                    "contact_id": contact.contact.id
                })
            return {
                "name": officer[0].officer.name,
                "reg_no": officer[0].officer.registration_number,
                "id_number": officer[0].officer.id_number,
                "title": officer[0].officer.job_title.id,
                "title_name": officer[0].officer.job_title.name,
                "contacts": contacts
            }
        return None

    @property
    def coordinates(self):
        try:
            return self.facility_coordinates_through
        except:
            return None

    @property
    def lat_long(self):
        coords = self.coordinates
        return [coords.coordinates.y, coords.coordinates.x] if coords else None

    def validate_closing_date_supplied_on_close(self):
        if self.closed and not self.closed_date:
            self.closed_date = timezone.now()
        elif self.closed and self.closed_date:
            now = timezone.now()
            if self.closed_date > now:
                raise ValidationError({
                    "closed_date": [
                        "The date of closing cannot be in the future"
                    ]
                })

    def validate_ward_and_sub_county(self):
        old_details = self.__class__.objects.get(id=self.id)

        if self.sub_county and not old_details.sub_county:
            if self.sub_county != self.ward.sub_county:
                raise ValidationError(
                    {
                        "ward": [
                            "The facility ward must be in "
                            " the selected sub-county"]
                    }
                )

    def ensure_closed_facility_operation_status_is_closed(self):
        # expects only one to be closed
        closed_fs = FacilityStatus.objects.get(name__search='closed')

        if self.closed:
            self.operation_status = closed_fs

        if self.operation_status == closed_fs:
            self.closed = True

        if self.closed and not self.closed_date:
            self.closed_date =  timezone.now()

    def ensure_operational_status_after_opening_facility(self):
        old_details = None
        try:
            old_details = Facility.objects.get(id=self.id)

        except Facility.DoesNotExist:
            return

        if old_details.closed  and not self.closed:
            operational_status = FacilityStatus.objects.get(name='Operational')
            self.operational_status = operational_status

    def clean(self, *args, **kwargs):
        self.validate_closing_date_supplied_on_close()
        #self.validate_ward_and_sub_county()
        # self.validate_facility_name()

        if self.closed:
            self.ensure_closed_facility_operation_status_is_closed()

        if not self.closed and self.pk:
            self.ensure_operational_status_after_opening_facility()
        super(Facility, self).clean()

    def _get_field_human_attribute(self, field_obj):
        if hasattr(field_obj, 'name'):
            return field_obj.name
        elif field_obj is True:
            return "Yes"
        elif field_obj is False:
            return "No"
        elif hasattr(field_obj, 'isoformat'):
            return field_obj.isoformat()
        else:
            return field_obj

    def _get_field_name(self, field):
        if hasattr(getattr(self, field), 'id'):
            field_name = field + "_id"
            return field_name
        else:
            return field

    def _get_field_data(self, field):
        if hasattr(getattr(self, field), 'id'):
            field_name = field + "_id"
            return str(getattr(self, field_name))
        elif hasattr(getattr(self, field), 'isoformat'):
            return getattr(self, field).isoformat()
        else:
            return getattr(self, field)

    def _get_display_field_name(self, field):
        if hasattr(getattr(self, field), 'id'):
            field_name = field + "_name"
            return field_name

        return field

    def _dump_updates(self, origi_model):
        fields = [field.name for field in self._meta.fields]
        forbidden_fields = [
            'closed', 'closing_reason', 'closed_date']
        data = []
        for field in fields:
            if (getattr(self, field) != getattr(origi_model, field) and
                    field not in forbidden_fields):
                field_data = getattr(self, field)
                updated_details = {
                    "display_value": self._get_field_human_attribute(
                        field_data),
                    "actual_value": self._get_field_data(field),
                    "display_field_name": self._get_display_field_name(field),
                    "field_name": self._get_field_name(field),
                    "human_field_name": field.replace("_", " ")
                }
                data.append(updated_details)

        if len(data):
            return json.dumps(data)
        else:
            message = "The facility was not scheduled for update"
            LOGGER.info(message)

    def index_facility_material_view(self):
        """
        Updates the search index with facilities in the material view

        Facilities are pushed to the material view via a trigger while
        search works at the django level and thus will not cater for
        updates on the material views.
        This function ensures that once a facility is saved, the
        search index is updated with the  respective record in the
        material view is updated
        """

        mat_view_facility_record = FacilityExportExcelMaterialView.objects.get(
            id=self.id)
        index_instance(
            "facilities",
            "FacilityExportExcelMaterialView",
            str(mat_view_facility_record.id)
        )

    def save(self, *args, **kwargs):  # NOQA
        """
        Override the save method in order to capture updates to a facility.
        This creates a record of the updates in the FacilityUpdates model.
        The updates will appear on the facility once the updates have been
        approved.
        """
        from facilities.serializers import FacilityDetailSerializer
        if not self.code and self.is_complete and self.approved_national_level:
            self.code = self.generate_next_code_sequence()
            self.push_new_facility()

        if not self.official_name:
            self.official_name = self.name

        if not self.is_complete and not self.is_approved:
            kwargs.pop('allow_save', None)
            super(Facility, self).save(*args, **kwargs)
            self.index_facility_material_view()
            self.update_facility_regulation_status()
            return

        if self.is_complete and not self.is_approved:
            kwargs.pop('allow_save', None)
            super(Facility, self).save(*args, **kwargs)
            self.index_facility_material_view()
            self.update_facility_regulation_status()
            return

        old_details = self.__class__.objects.get(id=self.id)

        # enable closing a facility
        if not old_details.closed and self.closed:
            self.is_published = False
            try:
                op_status = FacilityStatus.objects.get(name='Closed')
                self.operation_status = op_status
            except FacilityStatus.DoesNotExist:
                pass
            kwargs.pop('allow_save', None)
            super(Facility, self).save(*args, **kwargs)
            self.index_facility_material_view()
            return

        # enable opening a facility
        if old_details.closed and not self.closed:
            self.is_published = True
            kwargs.pop('allow_save', None)
            super(Facility, self).save(*args, **kwargs)
            self.index_facility_material_view()
            return

        old_details_serialized = FacilityDetailSerializer(
            old_details).data
        del old_details_serialized['updated']
        del old_details_serialized['created']
        del old_details_serialized['updated_by']
        new_details_serialized = FacilityDetailSerializer(self).data
        # del new_details_serialized['updated']
        del new_details_serialized['created']
        del new_details_serialized['updated_by']

        origi_model = self.__class__.objects.get(id=self.id)
        allow_save = kwargs.pop('allow_save', None)

        if allow_save:
            super(Facility, self).save(*args, **kwargs)
            self.index_facility_material_view()
            # self.update_facility_regulation_status()
        else:
            updates = self._dump_updates(origi_model)
            try:
                updates.pop('updated_by')
            except:
                pass

            # try:
            #     updates.pop('updated_by_id')
            # except:
            #     pass
            if updates:
                try:
                    facility_update = FacilityUpdates.objects.filter(
                        facility=self, cancelled=False, approved=False)[0]
                    try:
                        json_updates = json.loads(facility_update.facility_updates)
                    except TypeError:
                        json_updates = {}

                    recent_updates = json.loads(updates)

                    diffed_updates = []

                    changed_recent_fields = []
                    changed_older_fields = []
                    for record in json_updates:
                        for k, v in record.items():
                            if k == 'field_name':
                                if v not in changed_older_fields:
                                    changed_older_fields.append(v)
                                break

                    for record in recent_updates:
                        for k, v in record.items():
                            if k=='field_name':
                                if v not in changed_recent_fields:
                                    changed_recent_fields.append(v)
                                break

                    upated_upated_fields = list(set(
                        changed_older_fields).intersection(changed_recent_fields))
                    for record in json_updates:
                        for key, value in record.items():
                            if key == 'field_name' and value not in upated_upated_fields:
                                recent_updates.append(record)
                                break

                    merged_updates = recent_updates

                    facility_update.facility_updates = json.dumps(merged_updates)
                    facility_update.is_new = False
                    facility_update.save()
                except IndexError:
                    FacilityUpdates.objects.create(
                        facility_updates=updates, facility=self,
                        created_by=self.updated_by, updated_by=self.updated_by
                    ) if new_details_serialized != old_details_serialized \
                        else None

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'facilities'
        permissions = (
            ("view_classified_facilities", "Can see classified facilities"),
            ("view_closed_facilities", "Can see closed facilities"),
            ("view_rejected_facilities", "Can see rejected facilities"),
            ("publish_facilities", "Can publish facilities"),
            ("view_unpublished_facilities",
                "Can see the un published facilities"),
            ("view_unapproved_facilities",
                "Can see the unapproved facilities"),
            ("view_all_facility_fields",
                "Can see the all information on a facilities"),
        )


@reversion.register(follow=['facility'])
@encoding.python_2_unicode_compatible
class FacilityUpdates(AbstractBase):

    """
    Buffers facility updates until when they are approved upon
    which they reflect on the facility.
    """
    facility = models.ForeignKey(Facility, related_name='updates')
    approved = models.BooleanField(default=False)
    cancelled = models.BooleanField(default=False)
    facility_updates = models.TextField(null=True, blank=True)
    contacts = models.TextField(null=True, blank=True)
    services = models.TextField(null=True, blank=True)
    humanresources = models.TextField(null=True, blank=True)
    infrastructure = models.TextField(null=True, blank=True)
    officer_in_charge = models.TextField(null=True, blank=True)
    units = models.TextField(null=True, blank=True)
    geo_codes = models.TextField(null=True, blank=True)
    is_new = models.BooleanField(default=False)
    is_national_approval = models.BooleanField(default=False,
        help_text='Approval of the facility at the national level')
    dhis2_api_auth = DhisAuth()

    def facility_updated_json(self):
        updates = {}
        if self.facility_updates:
            updates['basic'] = json.loads(self.facility_updates)
        if self.services:
            updates['services'] = json.loads(self.services)
        if self.humanresources:
            updates['humanresources'] = json.loads(self.humanresources)
        if self.infrastructure:
            updates['infrastructure'] = json.loads(self.infrastructure)
        if self.contacts:
            updates['contacts'] = json.loads(self.contacts)
        if self.units:
            updates['units'] = json.loads(self.units)
        if self.officer_in_charge:
            updates['officer_in_charge'] = json.loads(self.officer_in_charge)
        if self.geo_codes:
            updates['geo_codes'] = json.loads(self.geo_codes)

        try:
            upgrade = FacilityUpgrade.objects.get(
                facility=self.facility, is_cancelled=False, is_confirmed=False)

            updates['upgrades'] = {
                "keph": upgrade.keph_level.name,
                "facility_type": upgrade.facility_type.name,
                "reason": upgrade.reason.reason
            }
        except FacilityUpgrade.DoesNotExist:
            pass

        return updates

    def approve_upgrades(self):
        try:
            upgrade = FacilityUpgrade.objects.get(
                facility=self.facility, is_cancelled=False, is_confirmed=False)

            upgrade.is_confirmed = True
            upgrade.save()
            self.facility.keph_level = upgrade.keph_level if \
                upgrade.keph_level else self.facility.keph_level
            self.facility.facility_type = upgrade.facility_type
            self.facility.save(allow_save=True)
        except FacilityUpgrade.DoesNotExist:
            pass

    def reject_upgrades(self):
        try:
            upgrade = FacilityUpgrade.objects.get(
                facility=self.facility, is_cancelled=False, is_confirmed=False)

            upgrade.is_cancelled = True
            upgrade.save()
        except FacilityUpgrade.DoesNotExist:
            pass

    def update_facility_has_edits(self):
        if not self.approved and not self.cancelled:
            self.facility.has_edits = True
        else:
            self.facility.has_edits = False
        # old_facility = Facility.objects.get(id=self.facility.id)

        # if self.facility_updates:
        #     data = json.loads(self.facility_updates)
        #     for field_changed in data:
        #         field_name = field_changed.get("field_name")
        #         old_value = getattr(old_facility, field_name)
        #         setattr(self.facility, field_name, old_value)
        self.facility.save(allow_save=True)

    def update_facility(self):
        if self.facility_updates:
            data = json.loads(self.facility_updates)
            for field_changed in data:
                field_name = field_changed.get("field_name")
                if field_name == 'date_established':
                    value = parser.parse(field_changed.get("actual_value"))
                    new_date = datetime.date(year=value.year, month=value.month, day=value.day)
                    value = new_date
                elif field_name == 'sub_county_id':
                    value = SubCounty.objects.get(id=field_changed.get('actual_value')).id
                else:
                    value = field_changed.get("actual_value")

                setattr(self.facility, field_name, value)
            self.facility.save(allow_save=True)
            if self.facility.code and self.facility.is_complete and self.facility.approved_national_level:
                self.facility.push_new_facility(self.facility.code)
            # self.push_facility_updates()


    def update_facility_services(self):
        from facilities.utils import create_facility_services
        services_to_add = json.loads(self.services)
        validated_data = {}
        validated_data['created'] = self.updated
        validated_data['updated'] = self.updated
        validated_data['created_by'] = self.created_by.id
        validated_data['updated_by'] = self.updated_by.id

        for service in services_to_add:

            try:
                FacilityService.objects.get(
                    service_id=service.get('service'), facility=self.facility)
            except FacilityService.DoesNotExist:
                create_facility_services(
                    self.facility, service, validated_data)

    def update_facility_humanresources(self):
        from facilities.utils import create_facility_humanresources
        humanresources_to_add = json.loads(self.humanresources)
        validated_data = {}
        validated_data['created'] = self.updated
        validated_data['updated'] = self.updated
        validated_data['created_by'] = self.created_by.id
        validated_data['updated_by'] = self.updated_by.id
        for hr in humanresources_to_add:
            try:
                FacilitySpecialist.objects.get(
                    speciality_id=hr.get('speciality'), facility=self.facility)
            except FacilitySpecialist.DoesNotExist:
                create_facility_humanresources(
                    self.facility, hr, validated_data)

    def update_facility_infrastructure(self):
        from facilities.utils import create_facility_infrastructure
        infrastructure_to_add = json.loads(self.infrastructure)
        validated_data = {}
        validated_data['created'] = self.updated
        validated_data['updated'] = self.updated
        validated_data['created_by'] = self.created_by.id
        validated_data['updated_by'] = self.updated_by.id
        for infra in infrastructure_to_add:
            try:
                FacilityInfrastructure.objects.get(
                    infrastructure_id=infra.get('infrastructure'), facility=self.facility)
            except FacilityInfrastructure.DoesNotExist:
                create_facility_infrastructure(
                    self.facility, infra, validated_data)

    def update_facility_contacts(self):
        from facilities.utils import create_facility_contacts
        contacts_to_add = json.loads(self.contacts)
        validated_data = {}
        validated_data['created'] = self.updated
        validated_data['updated'] = self.updated
        validated_data['created_by'] = self.created_by.id
        validated_data['updated_by'] = self.updated_by.id

        for contact in contacts_to_add:
            create_facility_contacts(self.facility, contact, validated_data)

    def update_facility_units(self):
        from facilities.utils import create_facility_units
        units_to_add = json.loads(self.units)
        validated_data = {}
        validated_data['created'] = self.updated
        validated_data['updated'] = self.updated
        validated_data['created_by'] = self.created_by.id
        validated_data['updated_by'] = self.updated_by.id
        for unit in units_to_add:
            create_facility_units(self.facility, unit, validated_data)

    def update_officer_in_charge(self):
        from facilities.utils import _create_officer
        officer_data = json.loads(self.officer_in_charge)
        user = self.created_by
        _create_officer(officer_data, user)

    def update_geo_codes(self):
        from mfl_gis.models import FacilityCoordinates
        if self.geo_codes and json.loads(self.geo_codes):
            data = {
                "facility_id": str(self.facility.id),
                "method_id": json.loads(self.geo_codes).get('method_id', None),
                "source_id": json.loads(self.geo_codes).get('source_id', None),
                "coordinates": json.loads(
                    self.geo_codes).get('coordinates', None),
                "created_by_id": self.created_by.id,
                "updated_by_id": self.updated_by.id,
                "created": self.updated
            }

            data['coordinates'] = Point(
                data['coordinates'].get('coordinates'))
            try:
                self.facility.facility_coordinates_through.id
                coords = self.facility.facility_coordinates_through
                for key, value in data.iteritems():
                    setattr(coords, key, value) if value else None
                coords.save()
            except:
                FacilityCoordinates.objects.create(**data)

    def validate_either_of_approve_or_cancel(self):
        error = "You can only approve or cancel and not both"
        if self.approved and self.cancelled:
            raise ValidationError(error)

    def validate_only_one_update_at_a_time(self):
        updates = self.__class__.objects.filter(
            facility=self.facility, approved=False,
            cancelled=False, is_new=False).count()
        if self.approved or self.cancelled:
            # No need to validate again as this is
            # an approval or rejection after the record was created first
            pass
        else:
            if updates >= 1 and self.is_new:
                error = ("The pending facility update has to be either"
                         "approved or canceled before another one is made")
                raise ValidationError(error)

    def push_facility_updates(self):
        from mfl_gis.models import FacilityCoordinates
        import re
        self.dhis2_api_auth.get_oauth2_token()

        dhis2_parent_id = self.dhis2_api_auth.get_parent_id(self.facility.ward.code)
        dhis2_org_unit_id = self.dhis2_api_auth.get_org_unit_id(self.facility.code)

        new_facility_updates_payload = {
            "code": str(self.facility.code),
            "name": str(self.facility.name),
            "shortName": str(self.facility.name),
            "displayName": str(self.facility.official_name),
            "parent": {
                "id": dhis2_parent_id
            },
            "openingDate": self.facility.date_established.strftime("%Y-%m-%d"),
            "coordinates": self.dhis2_api_auth.format_coordinates(
                re.search(r'\((.*?)\)', str(FacilityCoordinates.objects.values('coordinates')
                                            .get(facility_id=self.facility.id)['coordinates'])).group(1))
        }

        # print("Names;", "Official Name:", self.facility.official_name, "Name:", self.facility.name)
        #
        # print("New Facility Push Payload => ", new_facility_updates_payload)
        self.dhis2_api_auth.push_facility_updates_to_dhis2(dhis2_org_unit_id, new_facility_updates_payload)

    def clean(self, *args, **kwargs):
        self.validate_only_one_update_at_a_time()
        self.validate_either_of_approve_or_cancel()
        self.update_facility_has_edits()
        super(FacilityUpdates, self).clean()

    def save(self, *args, **kwargs):
        if self.approved and not self.cancelled:
            self.update_facility()
            self.update_facility_units() if self.units else None
            self.update_facility_contacts() if self.contacts else None
            self.update_facility_services() if self.services else None
            self.update_facility_humanresources() if self.humanresources else None
            self.update_facility_infrastructure() if self.infrastructure else None
            self.update_officer_in_charge() if self.officer_in_charge else None
            self.update_geo_codes() if self.update_geo_codes else None
            self.approve_upgrades()
            self.facility.has_edits = False
            self.facility.updated = timezone.now()
            self.facility.save(allow_save=True)
        if self.cancelled:
            self.reject_upgrades()

        super(FacilityUpdates, self).save(*args, **kwargs)

    def __str__(self):
        if self.approved and not self.cancelled:
            msg = "approved"
        elif self.cancelled:
            msg = "rejected"
        else:
            msg = "pending"
        return "{}: {}".format(self.facility, msg)


@reversion.register(follow=['operation_status', 'facility', ])
@encoding.python_2_unicode_compatible
class FacilityOperationState(AbstractBase):

    """
    logs changes to the operation_status of a facility.
    """
    operation_status = models.ForeignKey(
        FacilityStatus,
        help_text="Indicates whether the facility"
        "has been approved to operate, is operating, is temporarily"
        "non-operational, or is closed down",
        on_delete=models.PROTECT,)
    facility = models.ForeignKey(
        Facility, related_name='facility_operation_states',
        on_delete=models.PROTECT,)
    reason = models.TextField(
        null=True, blank=True,
        help_text='Additional information for the transition')

    def __str__(self):
        return "{}: {}".format(self.facility, self.operation_status)


@reversion.register
@encoding.python_2_unicode_compatible
class FacilityLevelChangeReason(AbstractBase):

    """
    Generic reasons for upgrading or downgrading a facility
    """
    reason = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.reason


@reversion.register(follow=['facility', 'facility_type', 'keph_level', 'reason'])  # noqa
@encoding.python_2_unicode_compatible
class FacilityUpgrade(AbstractBase):

    """
    Logs the upgrades and the downgrades of a facility.
    """
    facility = models.ForeignKey(Facility,
        related_name='facility_upgrades',
        on_delete=models.PROTECT,)
    facility_type = models.ForeignKey(FacilityType, on_delete=models.PROTECT,)
    keph_level = models.ForeignKey(
        KephLevel, null=True, blank=True, on_delete=models.PROTECT,)
    reason = models.ForeignKey(
        FacilityLevelChangeReason, on_delete=models.PROTECT,)
    is_confirmed = models.BooleanField(
        default=False,
        help_text='Indicates whether a facility upgrade or downgrade has been'
        ' confirmed')
    is_cancelled = models.BooleanField(
        default=False,
        help_text='Indicates whether a facility upgrade or downgrade has been'
        'canceled or not')
    is_upgrade = models.BooleanField(default=True)
    current_keph_level_name = models.CharField(
        max_length=100, null=True, blank=True)
    current_facility_type_name = models.CharField(
        max_length=100, null=True, blank=True)

    def validate_only_one_type_change_at_a_time(self):
        if self.is_confirmed or self.is_cancelled:
            pass
        else:
            type_change_count = self.__class__.objects.filter(
                facility=self.facility, is_confirmed=False, is_cancelled=False
            ).count()
            if type_change_count >= 1:
                error = ("The pending upgrade/downgrade has to be confirmed "
                         "first before another upgrade/downgrade is made")
                raise ValidationError(error)

    def populate_current_keph_level_and_facility_type(self):

        self.current_facility_type_name = self.facility.facility_type.name
        self.current_keph_level_name = self.facility.keph_level.name \
            if self.facility.keph_level else "N/A"

    def clean(self):
        super(FacilityUpgrade, self).clean()
        self.validate_only_one_type_change_at_a_time()
        self.populate_current_keph_level_and_facility_type()

    def save(self, *args, **kwargs):
        if not self.is_cancelled and not self.is_confirmed:
            self.facility.has_edits = True
            self.facility.save(allow_save=True)
        try:
            FacilityUpdates.objects.get(
                facility=self.facility, approved=False, cancelled=False)
        except FacilityUpdates.DoesNotExist:
            FacilityUpdates.objects.create(
                is_new=True, facility=self.facility,
                created_by=self.updated_by, updated_by=self.updated_by)

        super(FacilityUpgrade, self).save(*args, **kwargs)

    def __str__(self):
        return "{}: {} ({})".format(
            self.facility, self.facility_type, self.reason
        )


@reversion.register(follow=['facility', ])
@encoding.python_2_unicode_compatible
class FacilityApproval(AbstractBase):

    """
    Before a facility is visible to the public it is first approved
    at the county level.
    The user who approves a facility will be the same as the created_by field.
    """
    facility = models.ForeignKey(Facility, on_delete=models.PROTECT,)
    comment = models.TextField(null=True, blank=True)
    is_cancelled = models.BooleanField(
        default=False, help_text='Cancel a facility approval'
    )
    is_national_approval = models.BooleanField(default=False,
        help_text='Approval of the facility at the national level')

    def validate_rejection_comment(self):
        if self.is_cancelled and not self.comment:
            raise ValidationError(
                {
                    "rejection": ["A reason for the rejection is required"]
                }
            )

    def update_facility_rejection(self):
        if self.is_cancelled:
            self.facility.rejected = True
            self.facility.approved = False
        else:
            self.facility.rejected = False
            self.facility.approved = True
            self.facility.is_published = True
            if self.is_national_approval:
                self.facility.approved_national_level = True
        self.facility.save(allow_save=True)

    def clean(self, *args, **kwargs):
        self.validate_rejection_comment()
        self.facility.save(allow_save=True)
        self.update_facility_rejection()

    def __str__(self):
        msg = "rejected" if self.is_cancelled else "approved"
        return "{}: {}".format(self.facility, msg)


@reversion.register(follow=['facility_unit', 'regulation_status'])
@encoding.python_2_unicode_compatible
class FacilityUnitRegulation(AbstractBase):

    """
    Creates a facility units regulation status.
    A facility unit can have multiple regulation statuses
    but only one is active a time. The latest one is taken to the
    regulation status of the facility unit.
    """
    facility_unit = models.ForeignKey(
        'FacilityUnit', related_name='regulations', on_delete=models.PROTECT)
    regulation_status = models.ForeignKey(
        RegulationStatus, related_name='facility_units')

    def __str__(self):
        return "{}: {}".format(self.facility_unit, self.regulation_status)


@reversion.register(follow=['facility', 'unit'])
@encoding.python_2_unicode_compatible
class FacilityUnit(AbstractBase):

    """
    Autonomous units within a facility that are regulated differently from the
    facility.

    For example AKUH  is a facility and licensed by KMPDB.
    In AKUH there are other units such as its pharmacy which is licensed by
    PPB.
    The pharmacy will in this case be treated as a facility unit.
    """
    facility = models.ForeignKey(
        Facility, on_delete=models.PROTECT, related_name='facility_units')
    unit = models.ForeignKey(
        'FacilityDepartment', related_name='unit_facilities',
        on_delete=models.PROTECT)
    license_number = models.CharField(
        max_length=100, null=True, blank=True)
    registration_number = models.CharField(
        max_length=100, null=True, blank=True)

    @property
    def regulation_status(self):
        reg_statuses = FacilityUnitRegulation.objects.filter(
            facility_unit=self)
        return reg_statuses[0].regulation_status if reg_statuses else None

    def __str__(self):
        return "{}: {}".format(self.facility.name, self.unit.name)

    class Meta(AbstractBase.Meta):
        unique_together = ('facility', 'unit', )


@reversion.register(follow=['parent', ])
@encoding.python_2_unicode_compatible
class ServiceCategory(AbstractBase):

    """
    Categorization of health services. e.g Immunization, Antenatal,
    Family Planning etc.
    """
    name = models.CharField(
        max_length=100,
        help_text="What is the name of the category? ")
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='A short form of the category e.g ANC for antenatal')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        help_text='The parent category under which the category falls',
        related_name='sub_categories', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    @property
    def services_count(self):
        return len(self.category_services.all())

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'service categories'


@reversion.register
@encoding.python_2_unicode_compatible
class OptionGroup(AbstractBase):

    """
    Groups similar a options available to a service.
    E.g  options 1 to 6 could fall after KEPH level group
    """
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


@reversion.register(follow=['group'])
class Option(AbstractBase):

    """
    services could either be:
        Given in terms of KEPH levels:

        Similar services are offered in the different KEPH levels:
            For example, Environmental Health Services offered in KEPH level
            2 are similar to those offered in KEPH level 3. If the KEPH level
            of the facility is known, the corresponding KEPH level of the
            service should apply. If it is not known, write the higher KEPH
            level.

        Given through a choice of service level:
            For example, Oral Health Services are either Basic or Comprehensive

        A combination of choices and KEPH levels:
            For example, Mental Health Services are either Integrated or
            Specialised (and the Specialised Services are split into KEPH
            level).
    """
    value = models.TextField()
    display_text = models.CharField(max_length=30)
    is_exclusive_option = models.BooleanField(default=True)
    option_type = models.CharField(max_length=12, choices=(
        ('BOOLEAN', 'Yes/No or True/False responses'),
        ('INTEGER', 'Integral numbers e.g 1,2,3'),
        ('DECIMAL', 'Decimal numbers, may have a fraction e.g 3.14'),
        ('TEXT', 'Plain text'),
    ))
    group = models.ForeignKey(
        OptionGroup,
        help_text="The option group where the option lies",
        related_name='options', on_delete=models.PROTECT)

    def __str__(self):
        return "{}: {}".format(self.option_type, self.display_text)


@reversion.register(follow=['category', 'group', 'keph_level', ])
@encoding.python_2_unicode_compatible
class Service(SequenceMixin, AbstractBase):

    """
    A health service.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='A short form for the service e.g FANC for Focused '
        'Antenatal Care')
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.PROTECT,
        help_text="The classification that the service lies in.",
        related_name='category_services')
    code = SequenceField(unique=True, editable=False)
    group = models.ForeignKey(
        OptionGroup, on_delete=models.PROTECT,
        help_text="The option group containing service options")
    has_options = models.BooleanField(default=False)
    keph_level = models.ForeignKey(
        KephLevel, null=True, blank=True, on_delete=models.PROTECT,
        help_text="The KEPH level at which the service ought to be offered")

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_next_code_sequence()
        super(Service, self).save(*args, **kwargs)

    @property
    def category_name(self):
        return self.category.name

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'services'


@reversion.register(follow=['facility', 'option', 'service'])
@encoding.python_2_unicode_compatible
class FacilityService(AbstractBase):

    """
    A facility can have zero or more services.
    """
    facility = models.ForeignKey(
        Facility, related_name='facility_services',
        on_delete=models.PROTECT)
    option = models.ForeignKey(
        Option, null=True, blank=True, on_delete=models.PROTECT)
    is_confirmed = models.BooleanField(
        default=False,
        help_text='Indicates whether a service has been approved by the CHRIO')
    is_cancelled = models.BooleanField(
        default=False,
        help_text='Indicates whether a service has been canceled by the '
        'CHRIO')
    # For services that do not have options, the service will be linked
    # directly to the
    service = models.ForeignKey(Service, related_name='service_id', on_delete=models.PROTECT)

    @property
    def service_has_options(self):
        return True if self.option else False

    @property
    def number_of_ratings(self):
        return self.facility_service_ratings.count()

    @property
    def service_name(self):
            return self.service.name

    @property
    def option_display_value(self):
        return self.option.display_text

    @property
    def average_rating(self):
        avg = self.facility_service_ratings.aggregate(models.Avg('rating'))
        return avg['rating__avg'] or 0.0

    def __str__(self):
        if self.option:
            return "{}: {} ({})".format(
                self.facility, self.service, self.option
            )
        return "{}: {}".format(self.facility, self.service)

    def validate_unique_service_or_service_with_option_for_facility(self):

        if len(self.__class__.objects.filter(
                service=self.service, facility=self.facility,
                deleted=False)) == 1 and not self.deleted:
            error = {
                "service": [
                    ("The service {} has already been added to the "
                     "facility").format(self.service.name)]
            }
            raise ValidationError(error)

    def clean(self, *args, **kwargs):
        self.validate_unique_service_or_service_with_option_for_facility()


@reversion.register(follow=['facility_service', ])
@encoding.python_2_unicode_compatible
class FacilityServiceRating(AbstractBase):

    """Rating of a facility's service"""

    facility_service = models.ForeignKey(
        FacilityService, related_name='facility_service_ratings',
        on_delete=models.PROTECT,
    )
    rating = models.PositiveIntegerField(
        validators=[
            validators.MaxValueValidator(5),
            validators.MinValueValidator(0)
        ]
    )
    comment = models.TextField(null=True, blank=True)

    def __str__(self):
        return "{} - {}".format(self.facility_service, self.rating)


@reversion.register(follow=['facility', 'officer'])
@encoding.python_2_unicode_compatible
class FacilityOfficer(AbstractBase):

    """
    A facility can have more than one officer. This models links the two.
    """
    facility = models.ForeignKey(
        Facility, related_name='facility_officers',
        on_delete=models.PROTECT)
    officer = models.ForeignKey(
        Officer, related_name='officer_facilities', on_delete=models.PROTECT)

    class Meta(AbstractBase.Meta):
        unique_together = ('facility', 'officer')

    def __str__(self):
        return "{}: {}".format(self.facility, self.officer)


@reversion.register(follow=['regulatory_body'])
@encoding.python_2_unicode_compatible
class FacilityDepartment(AbstractBase):

    """
    Represents departments within a facility
    """
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    regulatory_body = models.ForeignKey(
        RegulatingBody, on_delete=models.PROTECT)

    def __str__(self):
        return self.name


@reversion.register(follow=['facility_type', 'owner'])
@encoding.python_2_unicode_compatible
class RegulatorSync(AbstractBase):

    """
    Stage facilities that are created initially in the Regulator system RHRIS
    before they are created in the MFL
    """
    name = models.CharField(
        max_length=100, help_text='The official name of the facility'
    )
    registration_number = models.CharField(
        max_length=100,
        help_text='The registration number given by the regulator')
    county = models.PositiveIntegerField(help_text='The code of the county')
    facility_type = models.ForeignKey(
        FacilityType,
        on_delete=models.PROTECT,
        help_text='The type of the facility e.g Medical Clinic')
    owner = models.ForeignKey(
        Owner, help_text='The owner of the facility', on_delete=models.PROTECT)
    regulatory_body = models.ForeignKey(
        RegulatingBody, help_text="The regulatory body the record came from",
        on_delete=models.PROTECT
    )
    mfl_code = models.PositiveIntegerField(
        null=True, blank=True, help_text='The assigned MFL code'
    )
    # sub_county, constituency, district, the, directors, the facility contact
    # inspectors_phone_number

    @property
    def county_name(self):
        county = County.objects.get(code=self.county)
        return county.name

    @property
    def probable_matches(self):
        """Retrieve probable facilities that match the sync's criteria"""
        query = Facility.objects.values('id', 'name', 'official_name', 'code')
        if self.mfl_code:
            return query.filter(code=self.mfl_code)

        # consider only alphanumerics for comparison of names
        alphanumerics = re.findall(r'[a-z0-9]+', self.name, re.IGNORECASE)
        name_filter = None
        for i in alphanumerics:
            f = models.Q(
                official_name__icontains=i) | models.Q(name__icontains=i)
            if name_filter is None:
                name_filter = f
            else:
                name_filter = name_filter | f

        if name_filter is not None:
            query = query.filter(name_filter)

        return query.filter(
            ward__constituency__county__code=self.county,
            owner=self.owner,
            regulatory_body=self.regulatory_body
        )

    def update_facility(self, facility):
        """Update a facility with registration number, update sync record
           with facility's mfl code
        """
        with transaction.atomic():
            facility.registration_number = self.registration_number
            self.mfl_code = facility.code
            facility.save(allow_save=True)
            self.save()
        return self

    def validate_county_exits(self):
        try:
            county = County.objects.get(code=self.county)
            return county.name
        except (County.DoesNotExist, ValueError):
            raise ValidationError(
                {
                    "county": ["County with provided code does not exist"]
                }
            )

    def clean(self):
        self.validate_county_exits()

    def __str__(self):
        return self.name


@reversion.register(follow=['parent'])
@encoding.python_2_unicode_compatible
class SpecialityCategory(AbstractBase):

    """
    Categorization of health specilaists. e.g Anesthesiologist, Gastroentologist,
    Radiologists etc.
    """
    name = models.CharField(
        max_length=100,
        help_text="What is the name of the category? ")
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='A short form of the category e.g ANC for antenatal')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        help_text='The parent category under which the category falls',
        related_name='sub_categories', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    @property
    def specialities_count(self):
        return len(self.category_services.all())

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'specialities categories'



@reversion.register(follow=['category'])
@encoding.python_2_unicode_compatible
class Speciality(SequenceMixin, AbstractBase):

    """
    Health specilities.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='A short form for the speciality'
        )
    category = models.ForeignKey(
        SpecialityCategory,
        on_delete=models.PROTECT,
        help_text="The classification that the specialities lies in.",
        related_name='category_specialities')
    code = SequenceField(unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_next_code_sequence()
        super(Speciality, self).save(*args, **kwargs)

    @property
    def category_name(self):
        return self.category.name

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'specialities'


@reversion.register(follow=['facility', 'speciality'])
@encoding.python_2_unicode_compatible
class FacilitySpecialist(AbstractBase):

    """
    A facility can have zero or more specialists.
    """
    facility = models.ForeignKey(
        Facility, related_name='facility_specialists',
        on_delete=models.PROTECT)

    speciality = models.ForeignKey(Speciality, related_name='speciality', on_delete=models.PROTECT,)

    count = models.IntegerField(
        default=0, 
        blank=True, 
        help_text='The actual number of specialists for this speciality.')

    @property
    def speciality_name(self):
            return self.speciality.name

    def __str__(self):
        return "{}: {}".format(self.facility, self.speciality)

    def validate_unique_speciality(self):

        if len(self.__class__.objects.filter(
                speciality=self.speciality, facility=self.facility,
                deleted=False)) == 1 and not self.deleted:
            error = {
                "speciality": [
                    ("The speciality {} has already been added to the "
                     "facility").format(self.speciality.name)]
            }
            raise ValidationError(error)

    def clean(self, *args, **kwargs):
        self.validate_unique_speciality()







####### infra
@reversion.register(follow=['parent'])
@encoding.python_2_unicode_compatible
class InfrastructureCategory(AbstractBase):

    """
    Categorization of health specilaists. e.g Anesthesiologist, Gastroentologist,
    Radiologists etc.
    """
    name = models.CharField(
        max_length=100,
        help_text="What is the name of the category? ")
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='A short form of the category e.g ANC for antenatal')
    parent = models.ForeignKey(
        'self', null=True, blank=True,
        help_text='The parent category under which the category falls',
        related_name='sub_categories', on_delete=models.PROTECT)

    def __str__(self):
        return self.name

    @property
    def specialities_count(self):
        return len(self.category_services.all())

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'specialities categories'



@reversion.register(follow=['category'])
@encoding.python_2_unicode_compatible
class Infrastructure(SequenceMixin, AbstractBase):

    """
    Health infrastructure.
    """
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(null=True, blank=True)
    abbreviation = models.CharField(
        max_length=50, null=True, blank=True,
        help_text='A short form for the infrastructure'
        )
    numbers = models.NullBooleanField(
        blank=True, null=True, default=True,
        help_text='A flag to indicate whether an infrastructure item can have count/numbers tracked ')
    category = models.ForeignKey(
        InfrastructureCategory,
        on_delete=models.PROTECT,
        help_text="The classification that the infrastructure item lies in.",
        related_name='category_infrastructure')
    code = SequenceField(unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.code:
            self.code = self.generate_next_code_sequence()
        super(Infrastructure, self).save(*args, **kwargs)

    @property
    def category_name(self):
        return self.category.name

    def __str__(self):
        return self.name

    class Meta(AbstractBase.Meta):
        verbose_name_plural = 'infrastructure'


@reversion.register(follow=['facility', 'infrastructure'])
@encoding.python_2_unicode_compatible
class FacilityInfrastructure(AbstractBase):

    """
    A facility can have zero or more infrastructure.
    """
    facility = models.ForeignKey(
        Facility, related_name='facility_infrastructure',
        on_delete=models.PROTECT)

    infrastructure = models.ForeignKey(
        Infrastructure,
        related_name='infrastructure',
            on_delete=models.PROTECT,)

    count = models.IntegerField(
        default=0, 
        blank=True, 
        help_text='The actual number of infrastructure items in a facility.')

    present = models.BooleanField(
        default=False, 
        help_text='True if the listed infrastructure is present.')

    @property
    def infrastructure_name(self):
            return self.infrastructure.name

    def __str__(self):
        return "{}: {}".format(self.facility, self.infrastructure)

    def validate_unique_infrastructure(self):

        if len(self.__class__.objects.filter(
                infrastructure=self.infrastructure, facility=self.facility,
                deleted=False)) == 1 and not self.deleted:
            error = {
                "infrastructure": [
                    ("The infrastructure {} has already been added to the "
                     "facility").format(self.infrastructure.name)]
            }
            raise ValidationError(error)

    def clean(self, *args, **kwargs):
        self.validate_unique_infrastructure()
####### infra
