from django.urls import path
from rest_framework import routers
from .views import IngestView, RunSummaryViewSet, TestResultViewSet

router = routers.DefaultRouter()
router.register("items", TestResultViewSet)
router.register("summaries", RunSummaryViewSet)

urlpatterns = router.urls + [
    path("ingest", IngestView.as_view(), name="results-ingest"),
]
