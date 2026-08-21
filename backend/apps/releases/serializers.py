from rest_framework import serializers

from .models import Iteration, Version


class VersionSerializer(serializers.ModelSerializer):
    iterations_count = serializers.SerializerMethodField()

    class Meta:
        model = Version
        fields = "__all__"

    def get_iterations_count(self, obj):
        return obj.iterations.count()


class IterationSerializer(serializers.ModelSerializer):
    version_name = serializers.CharField(source="version.name", read_only=True)
    cases_count = serializers.SerializerMethodField()

    class Meta:
        model = Iteration
        fields = "__all__"

    def get_cases_count(self, obj):
        return obj.cases.count()
