from django.urls import path

from .facility_reports import (
    ReportView,
    FacilityUpgradeDowngrade,
    CommunityHealthUnitReport
)

app_name = 'reporting'

urlpatterns = (
    path('chul/',
        CommunityHealthUnitReport.as_view(),
        name='chul_reports'),

    path('upgrades_downgrades/',
        FacilityUpgradeDowngrade.as_view(),
        name='upgrade_downgrade_report'),

    path('', ReportView.as_view(),
        name='reports'),

)
