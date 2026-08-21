from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.tasks.models import TaskRun

from .junit_parser import parse_junit_xml
from .models import RunSummary, TestResult
from .serializers import DashboardSerializer, IngestRequestSerializer, RunSummarySerializer, TestResultSerializer


class TestResultViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer
    filterset_fields = ["run", "result", "test_case"]
    ordering_fields = ["id", "duration_ms"]


class RunSummaryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RunSummary.objects.all()
    serializer_class = RunSummarySerializer
    lookup_field = "run_id"

    @action(detail=False, methods=["get"], url_path="dashboard")
    def dashboard(self, request):
        week_ago = timezone.now() - timedelta(days=7)
        qs = TaskRun.objects.all()
        last_week = qs.filter(created_at__gte=week_ago)
        by_status = {
            s["status"]: s["c"]
            for s in qs.values("status").annotate(c=Count("id"))
        }
        completed = qs.filter(status__in=["success", "failed"])
        pass_rate = (
            completed.filter(status="success").count() / completed.count()
            if completed.count() else 0.0
        )
        data = {
            "total_runs": qs.count(),
            "last_7d_runs": last_week.count(),
            "pass_rate_avg": round(pass_rate, 4),
            "by_status": by_status,
        }
        ser = DashboardSerializer(data)
        return Response(ser.data)


class IngestView(views.APIView):
    """接收 pytest junit 报告,解析后写 TestResult + RunSummary。
    由 Jenkinsfile 在 pytest 跑完后 POST 调用。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ser = IngestRequestSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        try:
            run = TaskRun.objects.get(id=d["run_id"])
        except TaskRun.DoesNotExist:
            return Response({"detail": f"run {d['run_id']} not found"}, status=404)

        # 优先用 inline XML,其次用文件路径
        xml_content = d.get("junit_xml")
        file_path = d.get("file_path")

        if d.get("allure_url"):
            run.jenkins_build_url = d["allure_url"]
            run.save(update_fields=["jenkins_build_url"])

        if xml_content:
            import tempfile
            with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as f:
                f.write(xml_content)
                tmp_path = f.name
            try:
                result = parse_junit_xml(tmp_path, run)
            finally:
                import os
                os.unlink(tmp_path)
        elif file_path:
            result = parse_junit_xml(file_path, run)
        else:
            return Response({"detail": "need junit_xml or file_path"}, status=400)

        return Response(result)
