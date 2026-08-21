"""把用例的步骤序列渲染为完整 pytest 脚本。
- 按 setup -> test -> teardown 三段输出
- 扫描所有步骤的 params,提取 $${name} 全局变量引用
- 在函数顶部注入全局变量初始化(静态值直接赋值,动态变量计算表达式)
- ${name} 局部变量不注入,假设用户在前面步骤赋值
"""
import re
from typing import Any

from apps.actionwords.renderer import extract_variable_refs, render_code
from apps.variables.crypto import decrypt_value, eval_dynamic
from apps.variables.models import Variable
from apps.testcases.models import TestCase, TestCaseStep


def _fn_name(case: TestCase) -> str:
    raw = (case.case_id or "case").lower()
    raw = re.sub(r"[^a-z0-9_]+", "_", raw)
    if not raw or raw[0].isdigit():
        raw = "case_" + raw
    if not raw.startswith("test_"):
        raw = "test_" + raw
    return raw


def _indent(code: str, n: int = 4) -> str:
    pad = " " * n
    return "\n".join(pad + line if line else line for line in code.splitlines())


def _collect_global_var_refs(steps: list[TestCaseStep]) -> list[str]:
    """从所有步骤的 params 字符串值里扫描 $${name} 引用。"""
    refs: set[str] = set()
    for s in steps:
        if not s.params:
            continue
        for v in _walk_values(s.params):
            if isinstance(v, str):
                g, _ = extract_variable_refs(v)
                refs.update(g)
    return sorted(refs)


def _walk_values(obj: Any):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from _walk_values(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _walk_values(v)
    else:
        yield obj


def _build_global_vars_init(case: TestCase, keys: list[str]) -> list[str]:
    """从数据库查全局变量,生成初始化代码行。"""
    if not keys:
        return []
    qs = Variable.objects.filter(scope="global", key__in=keys)
    by_key = {v.key: v for v in qs}

    lines: list[str] = []
    lines.append("    # === 全局变量 ===")
    for k in keys:
        v = by_key.get(k)
        if not v:
            lines.append(f"    {k} = None  # ponytail: 全局变量 {k} 未定义")
            continue
        if v.is_dynamic:
            expr = v.dynamic_expr or '""'
            lines.append(f"    {k} = {expr}  # 动态变量")
        else:
            val = decrypt_value(v.value) if v.is_encrypted else v.value
            lines.append(f"    {k} = {repr(val)}")
    lines.append("")
    return lines


def _indent_more(code: str, n: int = 4) -> str:
    """把已有的多行代码再整体加 n 空格缩进。"""
    pad = " " * n
    return "\n".join(pad + line if line else line for line in code.splitlines())


def render_test_function(case: TestCase, steps: list[TestCaseStep] | None = None) -> str:
    steps = list(steps if steps is not None else case.steps.all())
    sections: dict[str, list[TestCaseStep]] = {"setup": [], "test": [], "teardown": []}
    for s in steps:
        if not s.enabled:
            continue
        sections.setdefault(s.section, []).append(s)
    for k in sections:
        sections[k].sort(key=lambda s: (s.order, s.id))

    fn = _fn_name(case)
    has_setup_or_test = bool(sections["setup"] or sections["test"])
    has_teardown = bool(sections["teardown"])

    lines = [
        "import pytest",
        "",
        f"pytestmark = [pytest.mark.{case.type}]",
        "",
    ]

    # 函数签名:有数据交互就注入 cleanup + test_prefix
    params = ["http"]
    if has_setup_or_test:
        params.extend(["cleanup", "test_prefix"])
    lines.append(f"def {fn}({', '.join(params)}):")

    # 收集全局变量引用,在函数顶部注入初始化
    global_refs = _collect_global_var_refs(steps)
    body: list[str] = _build_global_vars_init(case, global_refs)

    # 数据隔离提示
    if has_setup_or_test:
        body.append("    # === 数据隔离 ===")
        body.append("    # 造数据后调 cleanup.append((\"DELETE\", path)) 或 track(http, cleanup, resp, \"DELETE\", \"/blog/{data.id}\")")
        body.append("    # 用例失败也会自动清理;数据带 f\"[{test_prefix}]\" 前缀避免并行冲突")
        body.append("")

    # 渲染 setup+test 段(原始缩进 4 空格)
    setup_test_lines: list[str] = []
    for section_key, title in [
        (TestCaseStep.SECTION_SETUP, "前置步骤"),
        (TestCaseStep.SECTION_TEST, "测试步骤"),
    ]:
        items = sections.get(section_key, [])
        if not items:
            continue
        setup_test_lines.append(f"# === {title} ===")
        for idx, step in enumerate(items, 1):
            name = step.name or step.action_word.name
            setup_test_lines.append(f"# step {idx}: {name}")
            if step.comment:
                for c in step.comment.splitlines():
                    setup_test_lines.append(f"# {c}")
            code = render_code(step.action_word, step.params or {})
            setup_test_lines.append(code)
            setup_test_lines.append("")

    # 渲染 teardown 段(原始缩进 4 空格)
    teardown_lines: list[str] = []
    if has_teardown:
        teardown_lines.append("# === 后置步骤(finally,保证执行) ===")
        for idx, step in enumerate(sections["teardown"], 1):
            name = step.name or step.action_word.name
            teardown_lines.append(f"# step {idx}: {name}")
            if step.comment:
                for c in step.comment.splitlines():
                    teardown_lines.append(f"# {c}")
            code = render_code(step.action_word, step.params or {})
            teardown_lines.append(code)
            teardown_lines.append("")

    # 组装:有 teardown 时用 try/finally 包裹,保证失败也执行
    if has_setup_or_test and has_teardown:
        body.append("    try:")
        body.append(_indent_more("\n".join(setup_test_lines), 8))
        body.append("    finally:")
        body.append(_indent_more("\n".join(teardown_lines), 8))
    elif has_setup_or_test:
        body.append(_indent("\n".join(setup_test_lines), 4))
    elif has_teardown:
        body.append(_indent("\n".join(teardown_lines), 4))
    else:
        body.append("    pass  # ponytail: 没有步骤,先占位")

    return "\n".join(lines) + "\n" + "\n".join(body) + "\n"
