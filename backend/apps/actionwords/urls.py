from rest_framework import routers
from .views import ActionWordViewSet

router = routers.DefaultRouter()
router.register("", ActionWordViewSet, basename="actionword")

urlpatterns = router.urls
