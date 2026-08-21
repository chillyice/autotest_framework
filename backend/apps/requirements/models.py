from django.db import models

from apps.projects.models import Project, TimestampedModel


class Requirement(TimestampedModel):
    """需求/故事,可关联外部 JIRA/禅道,也可纯本地维护。"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="requirements")
    title = models.CharField(max_length=256)
    ext_key = models.CharField(max_length=64, blank=True, help_text="外部系统编号,如 JIRA-1234")
    ext_url = models.URLField(blank=True)
    source = models.CharField(max_length=32, blank=True, help_text="jira/zentao/local")
    description = models.TextField(blank=True)
    status = models.CharField(max_length=32, default="open")

    class Meta:
        ordering = ["-id"]
        unique_together = ("project", "ext_key")

    def __str__(self):
        return f"{self.ext_key or self.title}"
