import os

from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import serializers

from .models import Script


class ScriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Script
        fields = "__all__"
        read_only_fields = ("last_synced_at",)

    def validate_file_path(self, value):
        # 防穿越:必须在仓库根下
        abs_path = os.path.normpath(os.path.join(settings.TEST_REPO_ROOT, value))
        if not abs_path.startswith(str(settings.TEST_REPO_ROOT)):
            raise ValidationError("file_path must be inside the test repo root")
        if not value.endswith(".py"):
            raise ValidationError("file_path must end with .py")
        return value


class ScriptContentSerializer(serializers.Serializer):
    content = serializers.CharField()


class ScriptSyncFromDiskSerializer(serializers.Serializer):
    """从磁盘扫描脚本入库的请求体(可选)。"""
    path = serializers.CharField(required=False, help_text="指定单文件,留空则全扫")
