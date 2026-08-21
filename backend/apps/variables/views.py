from django_filters import rest_framework as filters
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .crypto import decrypt_value, eval_dynamic
from .models import Environment, Variable, VariableCategory
from .serializers import (
    EnvironmentSerializer,
    VariableCategorySerializer,
    VariableSerializer,
    VariableTestDynamicSerializer,
)


class EnvironmentViewSet(viewsets.ModelViewSet):
    queryset = Environment.objects.all()
    serializer_class = EnvironmentSerializer
    search_fields = ["name"]


class VariableCategoryViewSet(viewsets.ModelViewSet):
    queryset = VariableCategory.objects.all()
    serializer_class = VariableCategorySerializer
    filterset_fields = ["project", "parent"]
    search_fields = ["name"]
    ordering_fields = ["id", "name", "path"]


class VariableFilter(filters.FilterSet):
    class Meta:
        model = Variable
        fields = ["scope", "project", "environment", "category", "key", "is_secret", "is_encrypted", "is_dynamic"]


class VariableViewSet(viewsets.ModelViewSet):
    queryset = Variable.objects.all()
    serializer_class = VariableSerializer
    filterset_class = VariableFilter
    search_fields = ["key", "description"]
    ordering_fields = ["scope", "key"]

    @action(detail=False, methods=["post"])
    def resolve(self, request):
        """批量解析变量真实值(给 codegen 用,会解密)。
        入参: {scope, project?, environment?, keys:[...]}
        出参: {key: {value, type, is_dynamic, dynamic_expr}}
        """
        scope = request.data.get("scope", "global")
        project = request.data.get("project")
        environment = request.data.get("environment")
        keys = request.data.get("keys") or []

        qs = Variable.objects.filter(scope=scope)
        if project:
            qs = qs.filter(project=project)
        if environment:
            qs = qs.filter(environment=environment)
        if keys:
            qs = qs.filter(key__in=keys)

        out = {}
        for v in qs:
            val = decrypt_value(v.value) if v.is_encrypted else v.value
            out[v.key] = {
                "value": val,
                "type": v.type,
                "is_dynamic": v.is_dynamic,
                "dynamic_expr": v.dynamic_expr if v.is_dynamic else "",
            }
        return Response(out)

    @action(detail=False, methods=["post"], url_path="test-dynamic")
    def test_dynamic(self, request):
        """测试动态表达式,返回计算结果。"""
        ser = VariableTestDynamicSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        expr = ser.validated_data["expr"]
        result = eval_dynamic(expr)
        return Response({"expr": expr, "result": str(result)})

    @action(detail=True, methods=["post"], url_path="reveal")
    def reveal(self, request, pk=None):
        """查看单个变量的真实值(需已认证)。"""
        v = self.get_object()
        val = decrypt_value(v.value) if v.is_encrypted else v.value
        if v.is_dynamic:
            val = str(eval_dynamic(v.dynamic_expr))
        return Response({"key": v.key, "value": val})
