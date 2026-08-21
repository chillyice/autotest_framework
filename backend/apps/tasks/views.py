import logging
from datetime import datetime

from django.conf import settings
from django.db import transaction
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.jenkins_client.client import JenkinsClient, JenkinsError

from .models import TaskRun, TestTask
from .serializers import TaskRunSerializer, TestTaskSerializer, TriggerSerializer

logger = logging.getLogger(__name__)


class TestTaskViewSet(viewsets.ModelViewSet):
    queryset = TestTask.objects.all()
    serializer_class = TestTaskSerializer
    filterset_fields = ["project", "status", "trigger", "owner"]
    search_fields = ["name"]
    ordering_fields = ["id", "name", "updated_at"]

    @action(detail=True, methods=["post"], serializer_class=TriggerSerializer)
    def trigger(self, request, pk=None):
        task = self.get_object()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        params = dict(ser.validated_data.get("params") or {})

        # 默认参数:基于任务用例反推 marker/keywords
        if task.cases.exists():
            types = set(task.cases.values_list("type", flat=True))
            if types == {"api"}:
                params.setdefault("SUITE", "api")
            elif types == {"ui"}:
                params.setdefault("SUITE", "ui")
            else:
                params.setdefault("SUITE", "all")

        env = task.environment
        if env:
            params.setdefault("API_BASE_URL", env.api_base_url)
            if env.ui_base_url:
                params.setdefault("UI_BASE_URL", env.ui_base_url)

        if not task.jenkins_job_name:
            return Response({"detail": "task has no jenkins_job_name bound"}, status=400)

        run = TaskRun.objects.create(
            task=task,
            jenkins_job_name=task.jenkins_job_name,
            status=TaskRun.STATUS_QUEUED,
            triggered_by=request.user if request.user.is_authenticated else None,
            params=params,
        )
        params["TASK_RUN_ID"] = run.id

        try:
            client = JenkinsClient()
            queue_id = client.trigger_build(task.jenkins_job_name, params)
            run.jenkins_queue_id = queue_id
            run.save(update_fields=["jenkins_queue_id"])

            # 同步等 build number(短超时,后续可由前端轮询 status 端点)
            build_no = client.queue_item_to_build(queue_id, timeout=30)
            if build_no:
                run.jenkins_build_number = build_no
                run.status = TaskRun.STATUS_RUNNING
                run.started_at = datetime.now()
                run.save(update_fields=["jenkins_build_number", "status", "started_at"])
        except JenkinsError as e:
            run.status = TaskRun.STATUS_ERROR
            run.error_message = str(e)
            run.save(update_fields=["status", "error_message"])
            return Response({"detail": str(e), "run_id": run.id}, status=502)

        return Response(TaskRunSerializer(run).data)

    @action(detail=True, methods=["get"])
    def runs(self, request, pk=None):
        task = self.get_object()
        runs = task.runs.all()[:20]
        return Response(TaskRunSerializer(runs, many=True).data)


class TaskRunViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TaskRun.objects.all()
    serializer_class = TaskRunSerializer
    filterset_fields = ["task", "status", "triggered_by"]
    ordering_fields = ["id", "started_at", "finished_at"]

    @action(detail=True, methods=["post"])
    def refresh(self, request, pk=None):
        """从 Jenkins 拉最新状态写回。"""
        run = self.get_object()
        if not run.jenkins_build_number:
            return Response({"detail": "no build number yet"}, status=400)
        try:
            client = JenkinsClient()
            info = client.get_build_info(run.jenkins_job_name, run.jenkins_build_number)
        except JenkinsError as e:
            return Response({"detail": str(e)}, status=502)

        mapping = {
            "SUCCESS": TaskRun.STATUS_SUCCESS,
            "FAILURE": TaskRun.STATUS_FAILED,
            "ABORTED": TaskRun.STATUS_ABORTED,
            None: TaskRun.STATUS_RUNNING,
        }
        new_status = mapping.get(info.result, TaskRun.STATUS_ERROR)
        run.status = new_status
        run.jenkins_build_url = info.url
        run.duration_ms = info.duration_ms
        if not info.building and not run.finished_at:
            run.finished_at = datetime.now()
        if not run.started_at and info.building:
            run.started_at = datetime.now()
        run.save()
        return Response(TaskRunSerializer(run).data)
