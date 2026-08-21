from django.urls import path

from .views import (
    BuildStatusView,
    CreateJobView,
    JobInfoView,
    TriggerBuildView,
)

urlpatterns = [
    path("jobs", CreateJobView.as_view(), name="jenkins-create-job"),
    path("jobs/<str:job_name>", JobInfoView.as_view(), name="jenkins-job-info"),
    path("builds/trigger", TriggerBuildView.as_view(), name="jenkins-trigger"),
    path("builds/status", BuildStatusView.as_view(), name="jenkins-build-status"),
]
