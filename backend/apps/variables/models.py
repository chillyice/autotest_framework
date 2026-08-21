from django.db import models

from apps.projects.models import Project, TimestampedModel

SCOPE_GLOBAL = "global"
SCOPE_PROJECT = "project"
SCOPE_ENV = "env"
SCOPES = [
    (SCOPE_GLOBAL, "全局"),
    (SCOPE_PROJECT, "项目"),
    (SCOPE_ENV, "环境"),
]

TYPE_STRING = "string"
TYPE_INT = "int"
TYPE_BOOL = "bool"
TYPE_JSON = "json"
TYPES = [
    (TYPE_STRING, "string"),
    (TYPE_INT, "int"),
    (TYPE_BOOL, "bool"),
    (TYPE_JSON, "json"),
]


class Environment(TimestampedModel):
    name = models.CharField(max_length=64, unique=True, help_text="如 dev/staging/prod")
    api_base_url = models.CharField(max_length=512)
    ui_base_url = models.CharField(max_length=512, blank=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class VariableCategory(TimestampedModel):
    """变量目录树,自引用。project 为空表示全局目录。"""
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="variable_categories")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="children")
    name = models.CharField(max_length=128)
    path = models.CharField(max_length=512, blank=True, help_text="完整路径,如 /shop/order")

    class Meta:
        ordering = ["path", "name"]
        unique_together = ("parent", "name")

    def __str__(self):
        return self.path or self.name


class Variable(TimestampedModel):
    """作用域链: global < project < env。同名后者覆盖前者。
    - is_secret: 敏感变量,API 返回 ***
    - is_encrypted: 存储级加密(Fernet),读取时解密
    - is_dynamic: 动态变量,value 字段存表达式,运行时计算
    """
    scope = models.CharField(max_length=16, choices=SCOPES, default=SCOPE_PROJECT)
    project = models.ForeignKey(Project, null=True, blank=True, on_delete=models.CASCADE, related_name="variables")
    environment = models.ForeignKey(Environment, null=True, blank=True, on_delete=models.CASCADE, related_name="variables")
    category = models.ForeignKey(VariableCategory, null=True, blank=True, on_delete=models.SET_NULL, related_name="variables")
    key = models.CharField(max_length=128)
    value = models.TextField(blank=True, help_text="静态值或动态表达式")
    type = models.CharField(max_length=8, choices=TYPES, default=TYPE_STRING)
    description = models.TextField(blank=True, help_text="备注")
    is_secret = models.BooleanField(default=False, help_text="保护:API 返回 ***")
    is_encrypted = models.BooleanField(default=False, help_text="加密:Fernet 存储级加密")
    is_dynamic = models.BooleanField(default=False, help_text="动态:value 是表达式,运行时计算")
    dynamic_expr = models.TextField(blank=True, help_text="动态表达式,如 datetime.now().strftime('%Y%m%d')")

    class Meta:
        ordering = ["scope", "key"]
        unique_together = ("scope", "project", "environment", "key")

    def __str__(self):
        return f"[{self.scope}] {self.key}"
