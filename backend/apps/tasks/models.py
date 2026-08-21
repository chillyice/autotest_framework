from django.conf import settings
from django.db import models

from apps.projects.models import Project, TimestampedModel
from apps.testcases.models import TestCase
from apps.variables.models import Environment

TASK_TRIGGER_MANUAL = "manual"
TASK_TRIGGER_CRON = "cron"
TASK_TRIGGER_WEBHOOK = "webhook"
TRIGGERS = [
    (TASK_TRIGGER_MANUAL, "手动"),
    (TASK_TRIGGER_CRON, "定时"),
    (TASK_TRIGGER_WEBHOOK, "Webhook"),
]

TASK_STATUS_DRAFT = "draft"
TASK_STATUS_ACTIVE = "active"
TASK_STATUS_ARCHIVED = "archived"
TASK_STATUS_CHOICES = [
    (TASK_STATUS_DRAFT, "草稿"),
    (TASK_STATUS_ACTIVE, "启用"),
    (TASK_STATUS_ARCHIVED, "归档"),
]


class TestTask(TimestampedModel):
    """测试任务:固定一组用例 + 环境 + Jenkins job 映射。
    触发即创建一条 TaskRun 记录,调 Jenkins API。
    """
    name = models.CharField(max_length=128)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    environment = models.ForeignKey(Environment, null=True, blank=True, on_delete=models.SET_NULL)
    cases = models.ManyToManyField(TestCase, related_name="tasks")
    trigger = models.CharField(max_length=16, choices=TRIGGERS, default=TASK_TRIGGER_MANUAL)
    cron_expr = models.CharField(max_length=64, blank=True, help_text="5字段 cron,如 0 2 * * *")
    status = models.CharField(max_length=16, choices=TASK_STATUS_CHOICES, default=TASK_STATUS_DRAFT)
    jenkins_job_name = models.CharField(max_length=128, blank=True)
    owner = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="tasks"
    )
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-id"]
        unique_together = ("project", "name")

    def __str__(self):
        return f"{self.project.key}-{self.name}"


class TaskRun(TimestampedModel):
    """单次执行记录。"""
    STATUS_QUEUED = "queued"
    STATUS_RUNNING = "running"
    STATUS_SUCCESS = "success"
    STATUS_FAILED = "failed"
    STATUS_ABORTED = "aborted"
    STATUS_ERROR = "error"
    STATUS_CHOICES = [
        (STATUS_QUEUED, "排队中"),
        (STATUS_RUNNING, "执行中"),
        (STATUS_SUCCESS, "成功"),
        (STATUS_FAILED, "失败"),
        (STATUS_ABORTED, "已取消"),
        (STATUS_ERROR, "异常"),
    ]

    task = models.ForeignKey(TestTask, on_delete=models.CASCADE, related_name="runs")
    jenkins_job_name = models.CharField(max_length=128, blank=True)
    jenkins_queue_id = models.IntegerField(null=True, blank=True)
    jenkins_build_number = models.IntegerField(null=True, blank=True)
    jenkins_build_url = models.URLField(blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_QUEUED)
    triggered_by = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL, related_name="task_runs"
    )
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    duration_ms = models.IntegerField(default=0)
    params = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Run#{self.id} {self.task.name}"
