from rest_framework import serializers

from apps.actionwords.models import ActionWord
from apps.actionwords.renderer import render_code

from .models import TestCase, TestCaseStep


class ActionWordBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActionWord
        fields = ["id", "name", "key", "category", "endpoint", "method", "parameters", "code_template"]


class TestCaseStepSerializer(serializers.ModelSerializer):
    action_word_detail = ActionWordBriefSerializer(source="action_word", read_only=True)
    rendered_code = serializers.SerializerMethodField()

    class Meta:
        model = TestCaseStep
        fields = "__all__"

    def get_rendered_code(self, obj):
        return render_code(obj.action_word, obj.params or {})


class TestCaseSerializer(serializers.ModelSerializer):
    requirements = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    steps = TestCaseStepSerializer(many=True, read_only=True)

    class Meta:
        model = TestCase
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from apps.requirements.models import Requirement
        self.fields["requirements"].child_relation.queryset = Requirement.objects.all()


class TestCaseStepWriteSerializer(serializers.ModelSerializer):
    """写专用:接受 action_word id,不嵌套返回。
    test_case 由父视图批量赋值,这里允许为空。
    """
    class Meta:
        model = TestCaseStep
        fields = "__all__"
        read_only_fields = ("test_case",)


class ReorderStepsSerializer(serializers.Serializer):
    """整体保存用例步骤顺序。
    steps 是 [{id?, action_word, section, order, name, params, enabled, comment}]
    id 为空表示新建。
    """
    steps = TestCaseStepWriteSerializer(many=True)


class GenerateScriptSerializer(serializers.Serializer):
    """把用例 + 步骤渲染为完整 pytest 脚本。"""
    test_case = serializers.IntegerField(required=False, help_text="已存在的用例 ID")
    title = serializers.CharField(required=False, help_text="新建用例标题")
    function_name = serializers.CharField(required=False, help_text="函数名,默认 test_<case_id>")
    file_path = serializers.CharField(required=False, help_text="落盘路径,留空只返代码")
    save_script = serializers.BooleanField(default=False, help_text="是否同步存为 Script 记录")
