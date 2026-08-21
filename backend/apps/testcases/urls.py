from rest_framework import routers

from .views import TestCaseStepViewSet, TestCaseViewSet

router = routers.DefaultRouter()
router.register("cases", TestCaseViewSet)
router.register("steps", TestCaseStepViewSet)

urlpatterns = router.urls
