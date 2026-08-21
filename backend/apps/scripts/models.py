import os

from django.conf import settings
from django.db import models

from apps.projects.models import Project, TimestampedModel

SCRIPT_TYPE_API = "api"
SCRIPT_TYPE_UI = "ui"
SCRIPT_TYPES = [(SCRIPT_TYPE_API, "API"), (SCRIPT_TYPE_UI, "UI")]


class Script(TimestampedModel):
    """脚本文件元数据 + 内容快照。
    file_path 相对仓库根,如 api/test_shop.py。
    content 是当前快照,保存时同步写盘。
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="scripts")
    test_case = models.OneToOneField(
        "testcases.TestCase", null=True, blank=True,
        on_delete=models.SET_NULL, related_name="script",
    )
    name = models.CharField(max_length=128)
    file_path = models.CharField(max_length=512, unique=True, help_text="相对仓库根的路径")
    type = models.CharField(max_length=8, choices=SCRIPT_TYPES, default=SCRIPT_TYPE_API)
    content = models.TextField(blank=True)
    last_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.file_path

    def absolute_path(self) -> str:
        return os.path.normpath(os.path.join(settings.TEST_REPO_ROOT, self.file_path))
