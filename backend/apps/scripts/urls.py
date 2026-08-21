from rest_framework import routers
from .views import ScriptViewSet

router = routers.DefaultRouter()
router.register("", ScriptViewSet, basename="script")

urlpatterns = router.urls
