from django_filters import rest_framework as filters
from rest_framework import viewsets

from .models import Iteration, Version
from .serializers import IterationSerializer, VersionSerializer


class VersionViewSet(viewsets.ModelViewSet):
    queryset = Version.objects.all()
    serializer_class = VersionSerializer
    filterset_fields = ["project", "status", "is_baseline"]
    search_fields = ["name", "description"]
    ordering_fields = ["id", "name", "release_date"]


class IterationViewSet(viewsets.ModelViewSet):
    queryset = Iteration.objects.all()
    serializer_class = IterationSerializer
    filterset_fields = ["project", "version", "status"]
    search_fields = ["name", "description"]
    ordering_fields = ["id", "start_date", "end_date"]
