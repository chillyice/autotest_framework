"""Jenkins 客户端封装:创建 job、触发 build、查询状态。
不引第三方 SDK,直接用 requests + REST API,避免 python-jenkins 在某些 Jenkins 版本上的兼容坑。
"""
import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class BuildInfo:
    number: int
    result: str  # SUCCESS / FAILURE / ABORTED / null(运行中)
    url: str
    duration_ms: int
    building: bool
    estimated_duration_ms: int = 0


class JenkinsError(Exception):
    pass


class JenkinsClient:
    def __init__(
        self,
        url: str | None = None,
        username: str | None = None,
        token: str | None = None,
        template_path: str | None = None,
    ):
        self.base_url = (url or settings.JENKINS_URL).rstrip("/")
        self.auth = (
            username or settings.JENKINS_USER,
            token or settings.JENKINS_TOKEN,
        )
        self.template_path = Path(
            template_path or settings.JENKINS_JOB_TEMPLATE
        )
        self._s = requests.Session()
        self._s.auth = self.auth
        self._s.headers["Accept"] = "application/json"
        self._crumb = self._fetch_crumb()  # ponytail: 单实例 crumb,够用

    def _fetch_crumb(self) -> dict | None:
        # 关闭 CSRF 保护的 Jenkins 没有也会返 200 + 空
        try:
            r = self._s.get(f"{self.base_url}/crumbIssuer/api/json", timeout=5)
            if r.ok and r.text:
                d = r.json()
                return {d["crumbRequestField"]: d["crumb"]}
        except requests.RequestException as e:
            logger.warning("jenkins crumb fetch failed: %s", e)
        return None

    def _post(self, path: str, **kwargs) -> requests.Response:
        if self._crumb:
            kwargs.setdefault("headers", {}).update(self._crumb)
        r = self._s.post(f"{self.base_url}{path}", **kwargs)
        if not r.ok and r.status_code not in (201, 302):
            raise JenkinsError(f"POST {path} -> {r.status_code}: {r.text[:300]}")
        return r

    def render_job_xml(
        self,
        *,
        description: str,
        suite: str = "all",
        api_base_url: str = "",
        ui_base_url: str = "",
        repo_url: str,
        repo_branch: str = "main",
        git_creds: str = "",
    ) -> str:
        tpl = self.template_path.read_text(encoding="utf-8")
        return tpl.format(
            description=description,
            suite=suite,
            api_base_url=api_base_url,
            ui_base_url=ui_base_url,
            repo_url=repo_url,
            repo_branch=repo_branch,
            git_creds=git_creds,
        )

    def create_or_update_job(self, job_name: str, xml: str) -> None:
        # 先试拿,有就 update,没有就 create
        exists = self._s.get(
            f"{self.base_url}/job/{job_name}/api/json", timeout=5
        )
        if exists.ok:
            self._post(
                f"/job/{job_name}/config.xml",
                data=xml,
                headers={"Content-Type": "application/xml"},
            )
            logger.info("jenkins job updated: %s", job_name)
        else:
            self._post(
                f"/createItem?name={job_name}",
                data=xml,
                headers={"Content-Type": "application/xml"},
            )
            logger.info("jenkins job created: %s", job_name)

    def trigger_build(self, job_name: str, params: dict[str, Any] | None = None) -> int:
        # 返回 queue item,需要查 actual build number
        q = self._post(
            f"/job/{job_name}/build",
            data=json.dumps(params or {}),
            headers={"Content-Type": "application/json"},
        )
        # Location: http://jenkins/queue/item/123/
        loc = q.headers.get("Location", "")
        if "/queue/item/" not in loc:
            raise JenkinsError(f"cannot parse queue item from {loc}")
        item = int(loc.rstrip("/").split("/")[-1])
        return item

    def queue_item_to_build(self, queue_item: int, timeout: int = 60) -> int | None:
        """轮询 queue item 拿到 executable.buildNumber。"""
        deadline = time.time() + timeout
        while time.time() < deadline:
            r = self._s.get(
                f"{self.base_url}/queue/item/{queue_item}/api/json", timeout=5
            )
            if r.ok:
                data = r.json()
                exe = data.get("executable")
                if exe and "number" in exe:
                    return int(exe["number"])
            time.sleep(2)
        return None

    def get_build_info(self, job_name: str, build_number: int) -> BuildInfo:
        r = self._s.get(
            f"{self.base_url}/job/{job_name}/{build_number}/api/json", timeout=10
        )
        if not r.ok:
            raise JenkinsError(f"get_build_info -> {r.status_code}")
        d = r.json()
        return BuildInfo(
            number=d["number"],
            result=d.get("result"),
            url=d["url"],
            duration_ms=d.get("duration", 0),
            building=d.get("building", False),
            estimated_duration_ms=d.get("estimatedDuration", 0),
        )

    def wait_for_build(self, job_name: str, build_number: int, timeout: int = 3600) -> BuildInfo:
        deadline = time.time() + timeout
        while time.time() < deadline:
            info = self.get_build_info(job_name, build_number)
            if not info.building:
                return info
            time.sleep(10)
        raise JenkinsError(f"build #{build_number} timed out after {timeout}s")

    def get_console(self, job_name: str, build_number: int, start: int = 0) -> str:
        r = self._s.get(
            f"{self.base_url}/job/{job_name}/{build_number}/logText/progressiveText",
            params={"start": start},
            timeout=15,
        )
        return r.text
