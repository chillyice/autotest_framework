"""AW 代码模板渲染:把 {{ var }} 替换为参数值,把 ${name}/$${name} 替换为 Python 变量引用。
- {{ var }}:AW 模板占位符,填入用户在步骤里设的参数值
- $${name}:全局变量引用,渲染为 Python 变量名 name,在 codegen 顶部注入初始化
- ${name}:局部变量引用,渲染为 Python 变量名 name(用户在前面的步骤自己赋值)
"""
import json
import re
from typing import Any

from .models import ActionWord

# AW 模板占位符
_AW_VAR_RE = re.compile(r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}")

# 全局变量 $${name}
_GLOBAL_RE = re.compile(r"\$\$\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}")

# 局部变量 ${name}  (注意不能匹配 $${...},放后面处理)
_LOCAL_RE = re.compile(r"(?<!\$)\$\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}")


def extract_variable_refs(text: str) -> tuple[list[str], list[str]]:
    """从一段文本里提取全局变量和局部变量引用名。"""
    if not text:
        return [], []
    globals_ = set(_GLOBAL_RE.findall(text))
    locals_ = set(_LOCAL_RE.findall(text))
    # 局部变量排除已被全局匹配的(因为 $${name} 的 ${name} 子串也会被 _LOCAL_RE 匹配到)
    locals_ -= globals_
    return sorted(globals_), sorted(locals_)


def render_code(aw: ActionWord, params: dict[str, Any] | None = None) -> str:
    """先填 AW 模板占位符 {{ var }}(把参数值渲染为 Python 表达式),
    再处理 $${} 和 ${}(整个值是变量引用时,渲染为变量名;混合字符串时渲染为 f-string)。
    """
    params = params or {}
    props = (aw.parameters or {}).get("properties", {})

    # 第一遍:填 AW 模板 {{ var }}
    def aw_repl(m: re.Match) -> str:
        name = m.group(1)
        val: Any = params.get(name)
        if val is None:
            schema = props.get(name, {})
            val = schema.get("default", "")
        return _py_expr(val)

    rendered = _AW_VAR_RE.sub(aw_repl, aw.code_template or "")
    return rendered


def _py_expr(val: Any) -> str:
    """把参数值渲染为 Python 表达式片段。
    - 整个值是 $${name} 或 ${name} -> 变量名
    - 混合字符串含变量引用 -> f-string
    - 字符串 -> repr
    - dict/list -> json
    - bool -> True/False
    - 数字 -> str
    """
    if val is None or val == "":
        return '""'
    if isinstance(val, str):
        return _string_to_py_expr(val)
    if isinstance(val, bool):
        return "True" if val else "False"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (dict, list)):
        # JSON 里嵌入变量:把 $${}/${} 替换为 Python 变量引用,输出 Python dict/list
        return _json_to_py_expr(val)
    return repr(val)


def _string_to_py_expr(s: str) -> str:
    """单个字符串参数 -> Python 表达式。"""
    # 完全匹配 $${name} 或 ${name}
    m = _GLOBAL_RE.fullmatch(s)
    if m:
        return m.group(1)
    m = _LOCAL_RE.fullmatch(s)
    if m:
        return m.group(1)

    # 含变量引用的混合字符串 -> f-string
    if _GLOBAL_RE.search(s) or _LOCAL_RE.search(s):
        # 把 $${name} 替换为 {name},${name} 替换为 {name}
        s2 = _GLOBAL_RE.sub(lambda m: "{" + m.group(1) + "}", s)
        s2 = _LOCAL_RE.sub(lambda m: "{" + m.group(1) + "}", s2)
        # 转义已有的 { } 字面量(非变量插值)—— ponytail: 简化,假设没有字面量花括号
        return "f" + repr(s2)

    # 普通字符串
    return repr(s)


def _json_to_py_expr(obj: Any) -> str:
    """dict/list 嵌入了 $${name}/${} 引用 -> 转 Python 字面量。
    最简做法:递归遍历,字符串字段按 _string_to_py_expr 渲染。
    """
    if isinstance(obj, dict):
        items = ", ".join(
            f"{json.dumps(k)}: {_json_to_py_expr(v)}" for k, v in obj.items()
        )
        return "{" + items + "}"
    if isinstance(obj, list):
        items = ", ".join(_json_to_py_expr(x) for x in obj)
        return "[" + items + "]"
    return _py_expr(obj)
