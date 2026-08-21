from django_filters import rest_framework as filters
from rest_framework import viewsets

from .models import Module, Project
from .serializers import ModuleSerializer, ProjectSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    search_fields = ["name", "key"]
    ordering_fields = ["id", "name"]


class ModuleFilter(filters.FilterSet):
    class Meta:
        model = Module
        fields = ["project", "parent"]


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    filterset_class = ModuleFilter
    search_fields = ["name"]
    ordering_fields = ["id", "name"]
