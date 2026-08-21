from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/login", TokenObtainPairView.as_view(), name="token_obtain"),
    path("api/auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/projects/", include("apps.projects.urls")),
    path("api/testcases/", include("apps.testcases.urls")),
    path("api/requirements/", include("apps.requirements.urls")),
    path("api/scripts/", include("apps.scripts.urls")),
    path("api/variables/", include("apps.variables.urls")),
    path("api/tasks/", include("apps.tasks.urls")),
    path("api/results/", include("apps.results.urls")),
    path("api/jenkins/", include("apps.jenkins_client.urls")),
    path("api/actionwords/", include("apps.actionwords.urls")),
    path("api/releases/", include("apps.releases.urls")),
    path("api/schema", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
