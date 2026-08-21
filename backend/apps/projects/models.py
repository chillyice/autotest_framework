from django.conf import settings
from django.db import models


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(TimestampedModel):
    name = models.CharField(max_length=128, unique=True)
    key = models.CharField(max_length=32, unique=True, help_text="项目短标识,如 SHOP")
    description = models.TextField(blank=True)
    repo_url = models.CharField(max_length=512, blank=True, help_text="测试仓库 git 地址")
    repo_branch = models.CharField(max_length=64, default="main")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.key}] {self.name}"


class Module(TimestampedModel):
    """用例模块树节点。parent 为空为根节点。"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="modules")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    name = models.CharField(max_length=128)
    path = models.CharField(max_length=512, blank=True, help_text="树路径,如 /shop/order")

    class Meta:
        unique_together = ("parent", "name")

    def __str__(self):
        return self.path or self.name
