"""OpenAPI 文档 -> ActionWord 解析器。
最简实现:用 PyYAML/JSON 解析,遍历 paths.operations,每个生成一个 AW。
"""
import json
import logging
import os
from pathlib import Path
from typing import Any

import yaml
from django.conf import settings

from .models import ActionWord

logger = logging.getLogger(__name__)


def _load_spec(spec_path: str | Path) -> dict:
    p = Path(spec_path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        return yaml.safe_load(text)
    return json.loads(text)


def _path_to_py(path: str) -> str:
    """/orders/{orderId} -> /orders/{orderId} (已是合法 f-string 表达)。"""
    return path


def _build_parameters(operation: dict, path_params: list, method: str, path: str) -> dict:
    """合并 path/query/body 参数成 schema。"""
    props: dict[str, Any] = {}
    required: list[str] = []

    for p in path_params:
        schema = p.get("schema", {})
        props[p["name"]] = {
            "type": schema.get("type", "string"),
            "description": p.get("description", ""),
            "in": "path",
            "default": schema.get("default", ""),
        }
        if p.get("required"):
            required.append(p["name"])

    op_params = operation.get("parameters", []) or []
    for p in op_params:
        loc = p.get("in", "query")
        schema = p.get("schema", {})
        props[p["name"]] = {
            "type": schema.get("type", "string"),
            "description": p.get("description", ""),
            "in": loc,
            "default": schema.get("default", ""),
        }
        if p.get("required"):
            required.append(p["name"])

    # requestBody: application/json
    body = operation.get("requestBody", {})
    json_content = (body.get("content", {}) or {}).get("application/json", {})
    if json_content:
        body_schema = json_content.get("schema", {})
        props["body"] = {
            "type": body_schema.get("type", "object"),
            "description": "请求体 JSON",
            "in": "body",
            "schema": body_schema,
        }
        if body.get("required"):
            required.append("body")

    return {"type": "object", "properties": props, "required": required}


def _build_code_template(method: str, path: str, parameters: dict) -> str:
    """生成 Jinja2 模板,渲染后形如:
        resp = http.request("POST", f"/orders/{order_id}", params={"q": q}, json=body)
    """
    props = parameters.get("properties", {})
    path_params = {n: p for n, p in props.items() if p.get("in") == "path"}
    query_params = {n: p for n, p in props.items() if p.get("in") == "query"}
    has_body = "body" in props

    # 把 path 里的 {orderId} 替换为 Python 变量名 orderId(orderId 已是合法标识符)
    py_path = path
    for name in path_params:
        py_path = py_path.replace("{" + name + "}", "{" + _safe_var(name) + "}")
    py_path_str = f"f\"{py_path}\"" if path_params else f'"{path}"'

    extras = []
    if query_params:
        keys = ", ".join(f'"{n}": {_safe_var(n)}' for n in query_params)
        extras.append(f"params={{{keys}}}")
    if has_body:
        extras.append("json=body")
    extras_str = (", " + ", ".join(extras)) if extras else ""

    return (
        f'resp = http.request("{method.upper()}", {py_path_str}{extras_str})\n'
        'assert resp.status_code in (200, 201, 204)'
    )


def _safe_var(name: str) -> str:
    """OpenAPI 参数名 -> 合法 Python 标识符。"""
    out = "".join(c if (c.isalnum() or c == "_") else "_" for c in name)
    if out and out[0].isdigit():
        out = "_" + out
    return out or "arg"


def _operation_name(operation: dict, method: str, path: str) -> tuple[str, str]:
    """返回 (name, key)。优先用 operationId。"""
    if operation.get("operationId"):
        key = operation["operationId"]
        name = operation.get("summary") or key
        return name, key
    # 没有 operationId,从 path 推
    parts = [p for p in path.strip("/").split("/") if not p.startswith("{")]
    base = parts[-1] if parts else "root"
    key = f"{method.lower()}_{base}".replace("-", "_")
    name = operation.get("summary") or f"{method.upper()} {path}"
    return name, key


def parse_spec_to_action_words(
    spec_path: str,
    project_id: int,
    *,
    overwrite: bool = True,
    category: str = "",
) -> dict:
    """解析 OpenAPI 文件,生成/更新 AW。返回统计。"""
    spec = _load_spec(spec_path)
    paths = spec.get("paths", {}) or {}
    created, updated, skipped = 0, 0, 0

    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue
        path_params = [p for p in (path_item.get("parameters") or []) if p.get("in") == "path"]

        for method, operation in path_item.items():
            if method.lower() not in ("get", "post", "put", "delete", "patch", "head", "options"):
                continue
            if not isinstance(operation, dict):
                continue

            name, key = _operation_name(operation, method, path)
            parameters = _build_parameters(operation, path_params, method, path)
            code_template = _build_code_template(method, path, parameters)

            aw, was_created = ActionWord.objects.update_or_create(
                project_id=project_id, key=key,
                defaults={
                    "name": name,
                    "category": category or operation.get("tags", [""])[0] if operation.get("tags") else "",
                    "description": operation.get("description", "") or operation.get("summary", ""),
                    "source": ActionWord.SOURCE_OPENAPI,
                    "endpoint": path,
                    "method": method.upper(),
                    "code_template": code_template,
                    "parameters": parameters,
                },
            )
            if was_created:
                created += 1
            else:
                updated += 1

    logger.info("parse_spec_to_action_words: created=%s updated=%s skipped=%s", created, updated, skipped)
    return {"created": created, "updated": updated, "skipped": skipped, "spec": str(spec_path)}


def find_specs() -> list[str]:
    """扫描 data/openapi/ 下所有 yaml/json。"""
    root = Path(settings.TEST_REPO_ROOT) / "data" / "openapi"
    if not root.exists():
        return []
    out = []
    for ext in ("*.yaml", "*.yml", "*.json"):
        out.extend(str(p) for p in root.glob(ext))
    return out
