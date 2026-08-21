from django_filters import rest_framework as filters
from rest_framework import viewsets

from .models import Requirement
from .serializers import RequirementSerializer


class ReqFilter(filters.FilterSet):
    class Meta:
        model = Requirement
        fields = ["project", "source", "status"]


class RequirementViewSet(viewsets.ModelViewSet):
    queryset = Requirement.objects.all()
    serializer_class = RequirementSerializer
    filterset_class = ReqFilter
    search_fields = ["title", "ext_key"]
    ordering_fields = ["id", "created_at"]
