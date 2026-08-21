from django.db import models

from apps.projects.models import Project, TimestampedModel


class ActionWord(TimestampedModel):
    """Action Word (AW):可复用的最小测试动作单元。
    来源:OpenAPI 解析 / 手动创建。
    每个 AW 携带一段 Jinja2 代码模板 + 参数 schema,用例编排时填参数后渲染成 Python 代码。
    """
    SOURCE_OPENAPI = "openapi"
    SOURCE_MANUAL = "manual"
    SOURCE_CHOICES = [
        (SOURCE_OPENAPI, "OpenAPI 解析"),
        (SOURCE_MANUAL, "手动创建"),
    ]

    SECTION_SETUP = "setup"
    SECTION_TEST = "test"
    SECTION_TEARDOWN = "teardown"
    SECTION_ANY = "any"
    SECTION_CHOICES = [
        (SECTION_ANY, "任意"),
        (SECTION_SETUP, "前置"),
        (SECTION_TEST, "测试"),
        (SECTION_TEARDOWN, "后置"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="action_words")
    name = models.CharField(max_length=128, help_text="AW 名称,如 创建订单")
    key = models.CharField(max_length=128, help_text="唯一 key,如 createOrder")
    category = models.CharField(max_length=64, blank=True, help_text="分组,如 订单/用户")
    description = models.TextField(blank=True)
    source = models.CharField(max_length=16, choices=SOURCE_CHOICES, default=SOURCE_MANUAL)
    suggested_section = models.CharField(
        max_length=16, choices=SECTION_CHOICES, default=SECTION_ANY,
        help_text="建议放置的步骤区",
    )

    # OpenAPI 来源元数据
    endpoint = models.CharField(max_length=256, blank=True, help_text="如 /orders/{id}")
    method = models.CharField(max_length=8, blank=True, help_text="GET/POST/...")

    # 模板 + 参数 schema
    code_template = models.TextField(
        blank=True,
        help_text="Jinja2 模板,渲染后是该 AW 在用例函数体里的一行/多行 Python 代码",
    )
    parameters = models.JSONField(
        default=dict, blank=True,
        help_text='参数 schema,{"properties":{...},"required":[...]}',
    )

    class Meta:
        ordering = ["category", "name"]
        unique_together = ("project", "key")

    def __str__(self):
        cat = self.category or "-"
        return f"[{cat}] {self.name} ({self.key})"
