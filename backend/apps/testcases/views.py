import os
from datetime import datetime

from django.conf import settings
from django.db import transaction
from django_filters import rest_framework as filters
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.scripts.models import Script

from .codegen import render_test_function
from .models import TestCase, TestCaseStep
from .serializers import (
    GenerateScriptSerializer,
    ReorderStepsSerializer,
    TestCaseSerializer,
    TestCaseStepSerializer,
    TestCaseStepWriteSerializer,
)


class CaseFilter(filters.FilterSet):
    class Meta:
        model = TestCase
        fields = ["project", "module", "type", "priority", "status", "version", "iteration"]


class TestCaseViewSet(viewsets.ModelViewSet):
    queryset = TestCase.objects.all()
    serializer_class = TestCaseSerializer
    filterset_class = CaseFilter
    search_fields = ["title", "case_id", "tags"]
    ordering_fields = ["id", "priority", "created_at"]

    @action(detail=True, methods=["get", "put"], serializer_class=ReorderStepsSerializer)
    def steps(self, request, pk=None):
        case = self.get_object()
        if request.method == "GET":
            steps = case.steps.all().order_by("section", "order", "id")
            return Response(TestCaseStepSerializer(steps, many=True).data)

        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        incoming = ser.validated_data["steps"]
        with transaction.atomic():
            incoming_ids = {s["id"] for s in incoming if s.get("id")}
            case.steps.exclude(id__in=incoming_ids).delete()
            for s in incoming:
                sid = s.pop("id", None)
                s["test_case"] = case
                if sid:
                    TestCaseStep.objects.filter(id=sid, test_case=case).update(**s)
                else:
                    TestCaseStep.objects.create(**s)
        steps = case.steps.all().order_by("section", "order", "id")
        return Response(TestCaseStepSerializer(steps, many=True).data)

    @action(detail=True, methods=["post"], serializer_class=GenerateScriptSerializer)
    def generate_script(self, request, pk=None):
        case = self.get_object()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data

        code = render_test_function(case)

        # 从 code 里提取函数名(第 4 行形如 "def test_xxx(http):")
        fn_name = case.case_id or "case"
        for line in code.splitlines():
            if line.strip().startswith("def "):
                fn_name = line.split("(")[0].split()[-1]
                break

        resp = {"code": code, "function_name": fn_name}

        if d.get("save_script") or d.get("file_path"):
            file_path = d.get("file_path") or f"api/test_{case.case_id.lower()}.py"
            abs_path = os.path.normpath(os.path.join(settings.TEST_REPO_ROOT, file_path))
            if not abs_path.startswith(str(settings.TEST_REPO_ROOT)):
                return Response({"detail": "file_path escapes repo root"}, status=400)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(code)
            script, _ = Script.objects.update_or_create(
                file_path=file_path,
                defaults={
                    "project": case.project,
                    "name": os.path.basename(file_path),
                    "type": case.type,
                    "content": code,
                    "last_synced_at": datetime.now(),
                    "test_case": case,
                },
            )
            resp["script_id"] = script.id
            resp["file_path"] = file_path

        return Response(resp)


class TestCaseStepViewSet(viewsets.ModelViewSet):
    queryset = TestCaseStep.objects.all()
    serializer_class = TestCaseStepSerializer
    filterset_fields = ["test_case", "section", "action_word", "enabled"]
    ordering_fields = ["section", "order", "id"]

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return TestCaseStepWriteSerializer
        return TestCaseStepSerializer
