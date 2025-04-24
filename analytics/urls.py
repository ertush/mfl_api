from django.urls import path

from .analytics_reports import (
    MatrixReportView
)

app_name = "analytics"

urlpatterns = (
    path('matrix-report/',
         MatrixReportView.as_view(),
         name='matrix-report'),

)
