from django.urls import path

from .analytics_reports import (
    MatrixReportView, DownloadReportView
)

app_name = "analytics"

urlpatterns = (
    path('matrix-report/',
         MatrixReportView.as_view(),
         name='matrix-report'),
    path('matrix-report-download/',
        DownloadReportView.as_view(),
        name='matrix-report-download'
         )

)
