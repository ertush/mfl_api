import json


from facilities.models import JobTitle, FacilityType
from django.core.management import BaseCommand

jts = [
    "Medical Superintendant",
    "Nursing Officer in Charge",
    "Hospital Director",
    "Clinical Officer",
    "Provincial Director - Medical Services (To Remove)",
    "Provincial Director - Public Health and Sanitation (to remove)",
    "Provincial Health Records and Information Officer - Medical Services",
    "Provincial Health Records and Information Officer - Public Health and Sanitation",
    "Provincial Public Health Nurse - Medical Services",
    "Provincial Public Health Nurse - Public Health and Sanitation",
    "Provincial Director - Medical Services",
    "Provincial Director - Public Health and Sanitation",
    "District Medical Officer of Health",
    "District Health Records and Information Officer",
    "District Public Health Nurse",
    "District Public Health Officer",
    "Doctor In Charge",
    "National HIS Facilitator",
    "System Configuration and Programming",
    "District Chief Health Administrative Officer",
    "Provincial Chief Health Administrative Officer - Public Health and Sanitation",
    "Unknown",
    "National MOH Officer",
    "Provincial Aids Co-Ordinator",
    "Provincial Director - Public Health and Sanitation",
    "National HIS Help Desk and Administration",
    "Director of Public Health and Sanitation",
    "County Health Records and Information Officer-MOH",
    "County Executive For Health"
]
f_type = """Health Centre
Dispensary
Other Hospital
Dental Clinic
Laboratory (Stand-alone)
Radiology Unit
VCT Centre (Stand-Alone)
Eye Centre
Funeral Home (Stand-alone)
Health Programme
Training Institution in Health (Stand-alone)
Blood Bank
Rural Health Training Centre
Rural Health Demonstration Centre
Eye Clinic
Regional Blood Transfusion Centre
Health Project
District Hospital
Provincial General Hospital
National Referral Hospital
Sub-District Hospital
Medical Clinic
Nursing Home
Maternity Home
Not in List
Medical Centre
Hospital
Health Centre
Dispensary
Maternity and Nursing Home
Medical Clinic
Other
Health Office
District Health Office
Provincial Health Office
National Health Office
District Health Office
National Health Office
"""


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        # for jt in jts:
        #     try:
        #         JobTitle.objects.get(name=jt)
        #     except JobTitle.DoesNotExist:
        #         print jt
        # 
        # 
        f_type_name = f_type.split('\n')
        print len(f_type_name)
        print FacilityType.objects.count()
        for name in f_type_name:
            try:
                FacilityType.objects.get(name=name)
                print name
            except FacilityType.DoesNotExist:
                pass
        print "=================================================="
        for obj in FacilityType.objects.all():
            if obj.name not in f_type_name:
                print obj.name
