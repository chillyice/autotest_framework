from rest_framework import routers

from .views import ModuleViewSet, ProjectViewSet

router = routers.DefaultRouter()
router.register("projects", ProjectViewSet)
router.register("modules", ModuleViewSet)

urlpatterns = router.urls
