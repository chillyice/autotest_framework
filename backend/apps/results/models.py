from django.db import models

from apps.tasks.models import TaskRun, TestTask
from apps.testcases.models import TestCase
from apps.projects.models import TimestampedModel

RESULT_PASSED = "passed"
RESULT_FAILED = "failed"
RESULT_SKIPPED = "skipped"
RESULT_ERROR = "error"
RESULT_CHOICES = [
    (RESULT_PASSED, "通过"),
    (RESULT_FAILED, "失败"),
    (RESULT_SKIPPED, "跳过"),
    (RESULT_ERROR, "异常"),
]


class TestResult(TimestampedModel):
    """单条用例在某次执行中的结果。"""
    run = models.ForeignKey(TaskRun, on_delete=models.CASCADE, related_name="results")
    test_case = models.ForeignKey(TestCase, null=True, blank=True, on_delete=models.SET_NULL)
    nodeid = models.CharField(max_length=256, help_text="pytest nodeid,如 api/test_x.py::test_y")
    title = models.CharField(max_length=256, blank=True)
    result = models.CharField(max_length=16, choices=RESULT_CHOICES)
    duration_ms = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    traceback = models.TextField(blank=True)
    allure_url = models.URLField(blank=True)

    class Meta:
        ordering = ["-id"]
        unique_together = ("run", "nodeid")

    def __str__(self):
        return f"{self.nodeid} {self.result}"


class RunSummary(models.Model):
    """冗余存一份汇总,Dashboard 查询用。"""
    run = models.OneToOneField(TaskRun, on_delete=models.CASCADE, related_name="summary")
    total = models.IntegerField(default=0)
    passed = models.IntegerField(default=0)
    failed = models.IntegerField(default=0)
    skipped = models.IntegerField(default=0)
    error = models.IntegerField(default=0)
    pass_rate = models.FloatField(default=0.0)

    def recompute(self):
        qs = self.run.results.all()
        self.total = qs.count()
        self.passed = qs.filter(result=RESULT_PASSED).count()
        self.failed = qs.filter(result=RESULT_FAILED).count()
        self.skipped = qs.filter(result=RESULT_SKIPPED).count()
        self.error = qs.filter(result=RESULT_ERROR).count()
        self.pass_rate = (self.passed / self.total) if self.total else 0.0
        self.save()
