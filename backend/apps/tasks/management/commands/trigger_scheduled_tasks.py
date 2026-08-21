"""扫描 status=cron 且到点的 TestTask,触发执行。
用法:
    python manage.py trigger_scheduled_tasks

配合系统 cron 每分钟跑一次:
    * * * * * cd /path/to/backend && .venv/bin/python manage.py trigger_scheduled_tasks >> /var/log/autotest_cron.log 2>&1

cron_expr 支持标准 5 字段: 分 时 日 月 周
"""
import logging
from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.jenkins_client.client import JenkinsClient, JenkinsError
from apps.tasks.models import TaskRun, TestTask

logger = logging.getLogger(__name__)


def _cron_match(expr: str, dt: datetime) -> bool:
    """简化版 cron 匹配:支持 * / 数字 / 逗号 /  ranges。
    不支持 step(*/N)和高级语法,够用。要完整换 croniter 库。
    """
    parts = expr.strip().split()
    if len(parts) != 5:
        return False
    minute, hour, day, month, weekday = parts
    fields = [
        (dt.minute, minute), (dt.hour, hour), (dt.day, day),
        (dt.month, month), (dt.weekday(), weekday),  # 0=Monday in Python
    ]
    # Python weekday(): Mon=0..Sun=6; cron: Sun=0..Sat=6
    # 转换:cron 的 0(Sun) 对应 Python 的 6
    py_wday = (dt.weekday() + 1) % 7
    fields[4] = (py_wday, weekday)

    for val, spec in fields:
        if not _field_match(val, spec):
            return False
    return True


def _field_match(val: int, spec: str) -> bool:
    if spec == "*":
        return True
    if "," in spec:
        return any(_field_match(val, s) for s in spec.split(","))
    if "-" in spec:
        lo, hi = spec.split("-", 1)
        return int(lo) <= val <= int(hi)
    return val == int(spec)


class Command(BaseCommand):
    help = "扫描到点的 cron 任务并触发 Jenkins 执行"

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="只打印不触发")

    def handle(self, *args, **options):
        dry = options["dry_run"]
        now = timezone.now()
        tasks = TestTask.objects.filter(trigger="cron", status="active")
        triggered, skipped, failed = 0, 0, 0

        for task in tasks:
            if not task.cron_expr:
                skipped += 1
                continue
            if not _cron_match(task.cron_expr, now):
                continue
            # 防重:同任务同分钟内不重复触发
            last = task.runs.filter(started_at__isnull=False).order_by("-started_at").first()
            if last and last.started_at and (now - last.started_at).total_seconds() < 90:
                skipped += 1
                continue

            self.stdout.write(f"[{now:%Y-%m-%d %H:%M}] trigger task #{task.id} {task.name}")
            if dry:
                continue

            try:
                self._trigger(task)
                triggered += 1
            except Exception as e:
                failed += 1
                logger.exception("trigger task %s failed: %s", task.id, e)

        self.stdout.write(self.style.SUCCESS(
            f"done: triggered={triggered} skipped={skipped} failed={failed} at {now:%H:%M}"
        ))

    def _trigger(self, task: TestTask):
        params = {}
        if task.cases.exists():
            types = set(task.cases.values_list("type", flat=True))
            if types == {"api"}:
                params["SUITE"] = "api"
            elif types == {"ui"}:
                params["SUITE"] = "ui"
            else:
                params["SUITE"] = "all"
        env = task.environment
        if env:
            params.setdefault("API_BASE_URL", env.api_base_url)
            if env.ui_base_url:
                params.setdefault("UI_BASE_URL", env.ui_base_url)

        with transaction.atomic():
            run = TaskRun.objects.create(
                task=task,
                jenkins_job_name=task.jenkins_job_name,
                status=TaskRun.STATUS_QUEUED,
                params=params,
            )
            params["TASK_RUN_ID"] = run.id

        client = JenkinsClient()
        queue_id = client.trigger_build(task.jenkins_job_name, params)
        run.jenkins_queue_id = queue_id
        run.save(update_fields=["jenkins_queue_id"])
