from rest_framework import serializers
from .models import Requirement


class RequirementSerializer(serializers.ModelSerializer):
    cases_count = serializers.SerializerMethodField()

    class Meta:
        model = Requirement
        fields = "__all__"

    def get_cases_count(self, obj):
        return obj.cases.count()
