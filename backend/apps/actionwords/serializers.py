from rest_framework import serializers
from .models import ActionWord


class ActionWordSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionWord
        fields = "__all__"


class ParseRequestSerializer(serializers.Serializer):
    spec_path = serializers.CharField(required=False, help_text="OpenAPI 文件路径,留空则扫描 data/openapi/")
    project = serializers.IntegerField()
    category = serializers.CharField(required=False, allow_blank=True, default="")
    overwrite = serializers.BooleanField(default=True)


class RenderRequestSerializer(serializers.Serializer):
    """单个 AW 渲染代码块。"""
    action_word = serializers.IntegerField()
    params = serializers.DictField(required=False)
