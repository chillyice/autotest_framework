from rest_framework import routers

from .views import TaskRunViewSet, TestTaskViewSet

router = routers.DefaultRouter()
router.register("tasks", TestTaskViewSet)
router.register("runs", TaskRunViewSet)

urlpatterns = router.urls
