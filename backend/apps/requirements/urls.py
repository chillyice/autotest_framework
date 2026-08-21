from rest_framework import routers
from .views import RequirementViewSet

router = routers.DefaultRouter()
router.register("", RequirementViewSet, basename="requirement")

urlpatterns = router.urls
