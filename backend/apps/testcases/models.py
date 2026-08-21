from django.db import models

from apps.projects.models import Module, Project, TimestampedModel

CASE_TYPE_API = "api"
CASE_TYPE_UI = "ui"
CASE_TYPES = [(CASE_TYPE_API, "API"), (CASE_TYPE_UI, "UI")]

PRIORITY = [(1, "P0"), (2, "P1"), (3, "P2"), (4, "P3")]

STATUS_DRAFT = "draft"
STATUS_READY = "ready"
STATUS_DEPRECATED = "deprecated"
STATUS_CHOICES = [
    (STATUS_DRAFT, "草稿"),
    (STATUS_READY, "就绪"),
    (STATUS_DEPRECATED, "废弃"),
]


class TestCase(TimestampedModel):
    """单条测试用例元数据。脚本实体由 Script 模型维护。"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="cases")
    module = models.ForeignKey(Module, null=True, blank=True, on_delete=models.SET_NULL, related_name="cases")
    requirements = models.ManyToManyField("requirements.Requirement", blank=True, related_name="cases")
    version = models.ForeignKey(
        "releases.Version", null=True, blank=True, on_delete=models.SET_NULL, related_name="cases",
    )
    iteration = models.ForeignKey(
        "releases.Iteration", null=True, blank=True, on_delete=models.SET_NULL, related_name="cases",
    )
    title = models.CharField(max_length=256)
    case_id = models.CharField(max_length=64, unique=True, help_text="用例编号,如 SHOP-001")
    type = models.CharField(max_length=8, choices=CASE_TYPES, default=CASE_TYPE_API)
    priority = models.IntegerField(choices=PRIORITY, default=2)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    tags = models.CharField(max_length=256, blank=True, help_text="逗号分隔")
    precondition = models.TextField(blank=True)
    expected = models.TextField(blank=True)

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"{self.case_id} {self.title}"


class TestCaseStep(TimestampedModel):
    """用例步骤:从 AW 库拖入,按区域(setup/test/teardown)和 order 排序。
    params 是该步骤填的参数值,渲染时传给 AW.code_template。
    """
    SECTION_SETUP = "setup"
    SECTION_TEST = "test"
    SECTION_TEARDOWN = "teardown"
    SECTION_CHOICES = [
        (SECTION_SETUP, "前置步骤"),
        (SECTION_TEST, "测试步骤"),
        (SECTION_TEARDOWN, "后置步骤"),
    ]

    test_case = models.ForeignKey(TestCase, on_delete=models.CASCADE, related_name="steps")
    action_word = models.ForeignKey(
        "actionwords.ActionWord", on_delete=models.CASCADE, related_name="case_steps",
    )
    section = models.CharField(max_length=16, choices=SECTION_CHOICES, default=SECTION_TEST)
    order = models.IntegerField(default=0)
    name = models.CharField(max_length=256, blank=True, help_text="步骤名,留空用 AW 名")
    params = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    comment = models.TextField(blank=True, help_text="步骤备注")

    class Meta:
        ordering = ["section", "order", "id"]
        unique_together = ("test_case", "section", "order")

    def __str__(self):
        return f"{self.test_case.case_id} [{self.section}] {self.name or self.action_word.name}"
