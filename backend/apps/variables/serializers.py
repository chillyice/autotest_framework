from rest_framework import serializers

from .models import Environment, Variable, VariableCategory
from .crypto import decrypt_value, encrypt_value, eval_dynamic


class EnvironmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Environment
        fields = "__all__"


class VariableCategorySerializer(serializers.ModelSerializer):
    children_count = serializers.SerializerMethodField()
    variables_count = serializers.SerializerMethodField()

    class Meta:
        model = VariableCategory
        fields = "__all__"

    def get_children_count(self, obj):
        return obj.children.count()

    def get_variables_count(self, obj):
        return obj.variables.count()


class VariableSerializer(serializers.ModelSerializer):
    """读:is_secret 返回 ***,is_encrypted 解密后返回 *** (因 secret 才加密)。
    写:is_encrypted=True 时对 value 加密后入库。
    """
    class Meta:
        model = Variable
        fields = "__all__"

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # 保护或加密的变量不返明文
        if instance.is_secret or instance.is_encrypted:
            ret["value"] = "***"
        return ret

    def create(self, validated):
        v = validated.get("value", "")
        if validated.get("is_encrypted") and v:
            validated["value"] = encrypt_value(v)
        return super().create(validated)

    def update(self, instance, validated):
        v = validated.get("value", None)
        if v is None:
            validated.pop("value", None)
        elif validated.get("is_encrypted", instance.is_encrypted) and v != "***":
            validated["value"] = encrypt_value(v)
        elif v == "***":
            validated.pop("value", None)
        return super().update(instance, validated)


class VariableResolveSerializer(serializers.Serializer):
    """运行时解析变量值(给 codegen 用)。"""
    scope = serializers.ChoiceField(choices=["global", "project", "env"])
    project = serializers.IntegerField(required=False)
    environment = serializers.IntegerField(required=False)
    keys = serializers.ListField(child=serializers.CharField(), help_text="要解析的变量 key 列表")


class VariableTestDynamicSerializer(serializers.Serializer):
    expr = serializers.CharField()
