from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.scripts.models import Script

from .models import ActionWord
from .parser import find_specs, parse_spec_to_action_words
from .renderer import render_code
from .serializers import ActionWordSerializer, ParseRequestSerializer, RenderRequestSerializer


class ActionWordViewSet(viewsets.ModelViewSet):
    queryset = ActionWord.objects.all()
    serializer_class = ActionWordSerializer
    filterset_fields = ["project", "category", "source", "suggested_section"]
    search_fields = ["name", "key", "category", "description"]
    ordering_fields = ["id", "category", "name"]

    @action(detail=False, methods=["post"], serializer_class=ParseRequestSerializer)
    def parse(self, request):
        """从 OpenAPI 文件解析生成 AW。"""
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        d = ser.validated_data
        spec_path = d.get("spec_path")
        if spec_path:
            paths = [spec_path]
        else:
            paths = find_specs()
        if not paths:
            return Response({"detail": "no openapi spec found under data/openapi/"}, status=400)

        results = []
        for p in paths:
            r = parse_spec_to_action_words(
                spec_path=p,
                project_id=d["project"],
                overwrite=d["overwrite"],
                category=d.get("category", ""),
            )
            results.append(r)
        return Response({"results": results})

    @action(detail=True, methods=["post"], serializer_class=RenderRequestSerializer)
    def render(self, request, pk=None):
        """渲染单个 AW 为代码块(预览用)。"""
        aw = self.get_object()
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)
        code = render_code(aw, ser.validated_data.get("params"))
        return Response({"code": code, "aw": ActionWordSerializer(aw).data})
