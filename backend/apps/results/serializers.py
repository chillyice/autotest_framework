from rest_framework import serializers
from .models import RunSummary, TestResult


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = "__all__"


class RunSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = RunSummary
        fields = "__all__"


class DashboardSerializer(serializers.Serializer):
    """仪表盘聚合。"""
    total_runs = serializers.IntegerField()
    last_7d_runs = serializers.IntegerField()
    pass_rate_avg = serializers.FloatField()
    by_status = serializers.DictField(child=serializers.IntegerField())


class IngestRequestSerializer(serializers.Serializer):
    """接收 pytest junit 报告。"""
    run_id = serializers.IntegerField(help_text="TaskRun ID,对应 Jenkins 参数 TASK_RUN_ID")
    junit_xml = serializers.CharField(required=False, help_text="junit XML 内容,与 file_path 二选一")
    file_path = serializers.CharField(required=False, help_text="服务端可访问的 XML 文件路径")
    allure_url = serializers.URLField(required=False, help_text="Allure 报告链接")
