from rest_framework import serializers
from .models import Project, Module


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = "__all__"


class ModuleSerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = "__all__"

    def get_children_count(self, obj):
        return obj.children.count()
