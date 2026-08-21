from rest_framework import routers
from .views import IterationViewSet, VersionViewSet

router = routers.DefaultRouter()
router.register("versions", VersionViewSet)
router.register("iterations", IterationViewSet)

urlpatterns = router.urls
