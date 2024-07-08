import argparse
import subprocess


def cleanFacility(model_id):
    from facilities.models import Facility

    qs = Facility.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityAdmissionStatus(model_id):
    from facilities.models import FacilityAdmissionStatus

    qs = FacilityAdmissionStatus.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityApproval(model_id):
    from facilities.models import FacilityApproval

    qs = FacilityApproval.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityContact(model_id):
    from facilities.models import FacilityContact

    qs = FacilityContact.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityDepartment(model_id):
    from facilities.models import FacilityDepartment

    qs = FacilityDepartment.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityExportExcelMaterialView(model_id):
    from facilities.models import FacilityExportExcelMaterialView

    qs = FacilityExportExcelMaterialView.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityInfrastructure(model_id):
    from facilities.models import FacilityInfrastructure

    qs = FacilityInfrastructure.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityKephManager(model_id):
    from facilities.models import FacilityKephManager

    qs = FacilityKephManager.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityLevelChangeReason(model_id):
    from facilities.models import FacilityLevelChangeReason

    qs = FacilityLevelChangeReason.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityOfficer(model_id):
    from facilities.models import FacilityOfficer

    qs = FacilityOfficer.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityOperationState(model_id):
    from facilities.models import FacilityOperationState

    qs = FacilityOperationState.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityRegulationStatus(model_id):
    from facilities.models import FacilityRegulationStatus

    qs = FacilityRegulationStatus.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityService(model_id):
    from facilities.models import FacilityService

    qs = FacilityService.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityServiceRating(model_id):
    from facilities.models import FacilityServiceRating

    qs = FacilityServiceRating.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilitySpecialist(model_id):
    from facilities.models import FacilitySpecialist

    qs = FacilitySpecialist.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityStatus(model_id):
    from facilities.models import FacilityStatus

    qs = FacilityStatus.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityType(model_id):
    from facilities.models import FacilityType

    qs = FacilityType.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityUnit(model_id):
    from facilities.models import FacilityUnit

    qs = FacilityUnit.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityUnitRegulation(model_id):
    from facilities.models import FacilityUnitRegulation

    qs = FacilityUnitRegulation.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityUpdates(model_id):
    from facilities.models import FacilityUpdates

    qs = FacilityUpdates.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanFacilityUpgrade (model_id):
    from facilities.models import FacilityUpgrade 

    qs = FacilityUpgrade .objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanOfficer(model_id):
    from facilities.models import Officer

    qs = Officer.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanOfficerContact(model_id):
    from facilities.models import OfficerContact

    qs = OfficerContact.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanKephLevel(model_id):
    from facilities.models import KephLevel

    qs = KephLevel.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanOptionGroup(model_id):
    from facilities.models import OptionGroup

    qs = OptionGroup.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanOption(model_id):
    from facilities.models import Option

    qs = Option.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanOwner(model_id):
    from facilities.models import Owner

    qs = Owner.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanOwnerType(model_id):
    from facilities.models import OwnerType

    qs = OwnerType.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanRegulatingBody(model_id):
    from facilities.models import RegulatingBody

    qs = RegulatingBody.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanRegulatingBodyContact(model_id):
    from facilities.models import RegulatingBodyContact

    qs = RegulatingBodyContact.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanRegulatoryBodyUser(model_id):
    from facilities.models import RegulatoryBodyUser

    qs = RegulatoryBodyUser.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanService(model_id):
    from facilities.models import Service

    qs = Service.objects.get(code=model_id)
    qs.deleted = True
    qs.save()

def cleanServiceCategory(model_id):
    from facilities.models import ServiceCategory

    qs = ServiceCategory.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanSpeciality(model_id):
    from facilities.models import Speciality

    qs = Speciality.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanSpecialityCategory(model_id):
    from facilities.models import SpecialityCategory

    qs = SpecialityCategory.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanInfrastructure(model_id):
    from facilities.models import Infrastructure

    qs = Infrastructure.objects.get(id=model_id)
    qs.deleted = True
    qs.save()

def cleanCounties(model_id):
    from common.models import County

    qs = County.objects.get(code=model_id)
    qs.deleted = True
    qs.save()

def cleanSubCounties(model_id):
    from common.models import SubCounty

    qs = SubCounty.objects.get(code=model_id)
    qs.deleted = True
    qs.save()

def cleanConstituencies(model_id):
    from common.models import Constituency

    qs = Constituency.objects.get(code=model_id)
    qs.deleted = True
    qs.save()

def cleanWards(model_id):
    from common.models import Ward

    qs = Ward.objects.get(code=model_id)
    qs.deleted = True
    qs.save()

def cleanInfrastructureCategory(model_id):
    from facilities.models import InfrastructureCategory

    qs = InfrastructureCategory.objects.get(id=model_id)
    qs.deleted = True
    qs.save()



def cleanClassException():
    raise cleanError("Unable to import requested model")


data_classes = {

        "Facility": cleanFacility,
        "FacilityAdmissionStatus": cleanFacilityAdmissionStatus,
        "FacilityApproval": cleanFacilityApproval,
        "FacilityContact": cleanFacilityContact,
        "FacilityDepartment": cleanFacilityDepartment,
        "FacilityExportExcelMaterialView": cleanFacilityExportExcelMaterialView,
        "FacilityInfrastructure": cleanFacilityInfrastructure,
        "FacilityKephManager": cleanFacilityKephManager,
        "FacilityLevelChangeReason": cleanFacilityLevelChangeReason,
        "FacilityOfficer": cleanFacilityOfficer,
        "FacilityOperationState": cleanFacilityOperationState,
        "FacilityRegulationStatus": cleanFacilityRegulationStatus,
        "FacilityService": cleanFacilityService,
        "FacilityServiceRating": cleanFacilityServiceRating,
        "FacilitySpecialist": cleanFacilitySpecialist,
        "FacilityStatus": cleanFacilityStatus,
        "FacilityType": cleanFacilityType,
        "FacilityUnit": cleanFacilityUnit,
        "FacilityUnitRegulation": cleanFacilityUnitRegulation,
        "FacilityUpdates": cleanFacilityUpdates,
        "FacilityUpgrade ": cleanFacilityUpgrade ,
        "Officer": cleanOfficer,
        "OfficerContact": cleanOfficerContact,
        "KephLevel": cleanKephLevel,
        "OptionGroup": cleanOptionGroup,
        "Option": cleanOption,
        "Owner": cleanOwner,
        "OwnerType": cleanOwnerType,
        "RegulatingBody": cleanRegulatingBody,
        "RegulatingBodyContact": cleanRegulatingBodyContact,
        "RegulatoryBodyUser": cleanRegulatoryBodyUser,
        "Service": cleanService,
        "ServiceCategory": cleanServiceCategory,
        "Speciality": cleanSpeciality,
        "SpecialityCategory": cleanSpecialityCategory,
        "Infrastructure": cleanInfrastructure,
        "InfrastructureCategory": cleanInfrastructureCategory,
        "County": cleanCounties,
        "SubCounty": cleanSubCounties,
        "Constituency": cleanConstituencies,
        "Ward": cleanWards

}
          


def run(model, data_class, uuids):
    if model == 'facilities':
        for uuid in uuids:
                data_classes.get(data_class, cleanClassException())(uuid)
                print ("[+] Successfully deleted {} in {}".format(uuid, data_class))
        print ("[+] Done")

def getParams():
    parser = argparse.ArgumentParser(description='soft delete parsed uuids')
    parser.add_argument('uuids', metavar='uuid', nargs='+', help='uuids to be deleted')
    parser.add_argument('--model', nargs=1, help='model name')
    parser.add_argument('--data_class', nargs=1, help='data class name')

    args = parser.parse_args()

    return tuple([args.uuids, args.model, args.data_class])

if __name__ == "__main__":
    params = getParams()
    uuids,[model],[data_class] = params[0], params[1], params[2]
    run(model, data_class, uuids)
    
    