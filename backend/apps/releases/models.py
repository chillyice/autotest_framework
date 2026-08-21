from django.db import models

from apps.projects.models import Project, TimestampedModel

VERSION_STATUS_OPEN = "open"
VERSION_STATUS_LOCKED = "locked"
VERSION_STATUS_ARCHIVED = "archived"
VERSION_STATUS_CHOICES = [
    (VERSION_STATUS_OPEN, "开放"),
    (VERSION_STATUS_LOCKED, "锁定"),
    (VERSION_STATUS_ARCHIVED, "归档"),
]

ITERATION_STATUS_PLANNING = "planning"
ITERATION_STATUS_ACTIVE = "active"
ITERATION_STATUS_CLOSED = "closed"
ITERATION_STATUS_CHOICES = [
    (ITERATION_STATUS_PLANNING, "计划中"),
    (ITERATION_STATUS_ACTIVE, "进行中"),
    (ITERATION_STATUS_CLOSED, "已结束"),
]


class Version(TimestampedModel):
    """产品版本,如 v1.0 / v2.3.0。
    锁定后用例不可改,适合发版后归档基线。
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="versions")
    name = models.CharField(max_length=64, help_text="如 v1.0")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=VERSION_STATUS_CHOICES, default=VERSION_STATUS_OPEN)
    release_date = models.DateField(null=True, blank=True)
    is_baseline = models.BooleanField(default=False, help_text="是否基线版本")

    class Meta:
        ordering = ["-id"]
        unique_together = ("project", "name")

    def __str__(self):
        return f"{self.project.key}-{self.name}"


class Iteration(TimestampedModel):
    """迭代/Sprint,关联到版本,有起止时间。"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="iterations")
    version = models.ForeignKey(Version, null=True, blank=True, on_delete=models.SET_NULL, related_name="iterations")
    name = models.CharField(max_length=128, help_text="如 2024Q1Sprint3")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=16, choices=ITERATION_STATUS_CHOICES, default=ITERATION_STATUS_PLANNING)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["-id"]
        unique_together = ("project", "name")

    def __str__(self):
        return f"{self.project.key}-{self.name}"
