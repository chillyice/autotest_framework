"""解析 pytest 产出的 junit XML,写入 TestResult + RunSummary。
pytest 加 --junitxml=target/report.xml 即可产出。
"""
import logging
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from apps.testcases.models import TestCase

from .models import (
    RESULT_ERROR,
    RESULT_FAILED,
    RESULT_PASSED,
    RESULT_SKIPPED,
    RunSummary,
    TestResult,
)

logger = logging.getLogger(__name__)

# nodeid 形如 api/test_x.py::test_y 或 api/test_x.py::TestCls::test_y
_CASE_ID_RE = re.compile(r"test_([a-zA-Z0-9_]+)")


def _map_result(junit_status: str, has_error: bool) -> str:
    """junit <testcase> 里子标签决定结果。"""
    if has_error:
        return RESULT_ERROR
    if junit_status == "failure":
        return RESULT_FAILED
    if junit_status == "skipped":
        return RESULT_SKIPPED
    return RESULT_PASSED


def _extract_case_id(nodeid: str) -> str | None:
    """从 nodeid 反推 case_id。
    nodeid: api/test_shop_001.py::test_shop_001  ->  shop_001
    """
    m = _CASE_ID_RE.search(nodeid)
    if not m:
        return None
    return m.group(1)


def parse_junit_xml(xml_path: str, run) -> dict:
    """解析 junit XML,写 TestResult + 重算 RunSummary。返回统计。"""
    p = Path(xml_path)
    if not p.exists():
        return {"error": f"file not found: {xml_path}"}

    try:
        tree = ET.parse(p)
    except ET.ParseError as e:
        return {"error": f"xml parse failed: {e}"}

    root = tree.getroot()
    # 兼容 testsuites 包一层 和 直接 testsuite
    suites = root.findall(".//testsuite") if root.tag == "testsuites" else [root]

    created, updated, failed_count = 0, 0, 0

    for suite in suites:
        for tc in suite.findall("testcase"):
            nodeid = tc.get("name", "")
            classname = tc.get("classname", "")
            # 拼 nodeid: file::class::name
            file_attr = tc.get("file") or classname
            full_nodeid = f"{file_attr}::{nodeid}" if file_attr else nodeid

            time_s = float(tc.get("time", "0") or "0")
            duration_ms = int(time_s * 1000)

            # 找子标签判断结果
            failure = tc.find("failure")
            error = tc.find("error")
            skipped = tc.find("skipped")

            if error is not None:
                status = RESULT_ERROR
                err_msg = error.get("message", "") or error.text or ""
                tb = error.text or ""
            elif failure is not None:
                status = RESULT_FAILED
                err_msg = failure.get("message", "") or failure.text or ""
                tb = failure.text or ""
            elif skipped is not None:
                status = RESULT_SKIPPED
                err_msg = skipped.get("message", "") or ""
                tb = ""
            else:
                status = RESULT_PASSED
                err_msg = ""
                tb = ""

            if status in (RESULT_FAILED, RESULT_ERROR):
                failed_count += 1

            # 反查 TestCase(按 case_id)
            case_id = _extract_case_id(full_nodeid)
            test_case = None
            if case_id:
                test_case = TestCase.objects.filter(case_id__iexact=case_id).first()

            obj, created_flag = TestResult.objects.update_or_create(
                run=run, nodeid=full_nodeid,
                defaults={
                    "test_case": test_case,
                    "title": nodeid,
                    "result": status,
                    "duration_ms": duration_ms,
                    "error_message": err_msg[:8000],
                    "traceback": tb[:16000],
                },
            )
            if created_flag:
                created += 1
            else:
                updated += 1

    # 重算汇总
    summary, _ = RunSummary.objects.get_or_create(run=run)
    summary.recompute()

    # 同步更新 TaskRun 状态(失败结果 -> failed)
    if failed_count > 0 and run.status not in ("failed", "error"):
        run.status = "failed"
        run.save(update_fields=["status"])
    elif failed_count == 0 and run.status == "running":
        run.status = "success"
        run.save(update_fields=["status"])

    return {
        "created": created,
        "updated": updated,
        "failed": failed_count,
        "total": summary.total,
        "passed": summary.passed,
        "pass_rate": round(summary.pass_rate, 4),
    }
