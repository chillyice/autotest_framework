import os
from datetime import datetime

from django.conf import settings
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Script
from .serializers import ScriptContentSerializer, ScriptSerializer


class ScriptViewSet(viewsets.ModelViewSet):
    queryset = Script.objects.all()
    serializer_class = ScriptSerializer
    filterset_fields = ["project", "type", "test_case"]
    search_fields = ["name", "file_path"]
    ordering_fields = ["id", "name", "updated_at"]

    def perform_create(self, serializer):
        instance = serializer.save()
        self._write_to_disk(instance)

    def perform_update(self, serializer):
        instance = serializer.save()
        self._write_to_disk(instance)

    def perform_destroy(self, instance):
        # ponytail: 库里删,磁盘文件保留由 git 管理,避免误删源码
        instance.delete()

    @action(detail=True, methods=["get", "put"], serializer_class=ScriptContentSerializer)
    def content(self, request, pk=None):
        script = self.get_object()
        if request.method == "GET":
            # 优先返DB快照,带磁盘最新可选
            return Response({"content": script.content})
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        script.content = ser.validated_data["content"]
        script.last_synced_at = datetime.now()
        script.save(update_fields=["content", "last_synced_at", "updated_at"])
        self._write_to_disk(script)
        return Response({"content": script.content})

    @action(detail=False, methods=["post"], url_path="sync-from-disk")
    def sync_from_disk(self, request):
        """扫描仓库 api/ ui/ 下 .py 文件,入库或更新 content。"""
        scanned, updated = 0, 0
        for sub in ("api", "ui"):
            root = os.path.join(settings.TEST_REPO_ROOT, sub)
            for dirpath, _dirs, files in os.walk(root):
                if "__pycache__" in dirpath or os.path.basename(dirpath) == "client":
                    continue
                for fn in files:
                    if not fn.startswith("test_") or not fn.endswith(".py"):
                        continue
                    abs_path = os.path.normpath(os.path.join(dirpath, fn))
                    rel = os.path.relpath(abs_path, settings.TEST_REPO_ROOT).replace("\\", "/")
                    with open(abs_path, "r", encoding="utf-8") as f:
                        body = f.read()
                    obj, created = Script.objects.update_or_create(
                        file_path=rel,
                        defaults={"name": fn, "content": body, "last_synced_at": datetime.now()},
                    )
                    scanned += 1
                    updated += 0 if created else 1
        return Response({"scanned": scanned, "updated": updated, "created": scanned - updated})

    @staticmethod
    def _write_to_disk(script: Script):
        abs_path = script.absolute_path()
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(script.content)
