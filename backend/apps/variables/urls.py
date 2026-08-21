from rest_framework import routers
from .views import EnvironmentViewSet, VariableCategoryViewSet, VariableViewSet

router = routers.DefaultRouter()
router.register("envs", EnvironmentViewSet)
router.register("categories", VariableCategoryViewSet)
router.register("", VariableViewSet, basename="variable")

urlpatterns = router.urls
