from rest_framework import serializers

from apps.testcases.models import TestCase
from .models import TaskRun, TestTask


class TestTaskSerializer(serializers.ModelSerializer):
    cases = serializers.PrimaryKeyRelatedField(many=True, queryset=TestCase.objects.none())
    case_count = serializers.SerializerMethodField()
    last_run_status = serializers.SerializerMethodField()

    class Meta:
        model = TestTask
        fields = "__all__"
        read_only_fields = ("owner",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["cases"].child_relation.queryset = TestCase.objects.all()

    def get_case_count(self, obj):
        return obj.cases.count()

    def get_last_run_status(self, obj):
        last = obj.runs.first()
        return last.status if last else None

    def create(self, validated):
        user = self.context["request"].user
        if user and user.is_authenticated:
            validated["owner"] = user
        return super().create(validated)


class TaskRunSerializer(serializers.ModelSerializer):
    task_name = serializers.CharField(source="task.name", read_only=True)

    class Meta:
        model = TaskRun
        fields = "__all__"
        read_only_fields = (
            "jenkins_queue_id", "jenkins_build_number", "jenkins_build_url",
            "status", "started_at", "finished_at", "duration_ms", "error_message",
        )


class TriggerSerializer(serializers.Serializer):
    params = serializers.DictField(required=False, help_text="覆盖 Jenkins job 参数")
