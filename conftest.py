import re
import uuid
from contextlib import contextmanager

import pytest

from common.config import settings
from common.http_client import HttpClient
from common.logger import logger


@pytest.fixture(scope="session")
def http_base():
    """无 token 的基础 client,仅用于登录接口。"""
    client = HttpClient(base_url=settings.api_base_url)
    logger.info("http_base ready: %s", settings.api_base_url)
    yield client
    client.close()


@pytest.fixture(scope="session")
def auth_factory(http_base):
    """登录工厂:按邮箱密码登录,缓存 session 级 client。

    用法:
        auth = auth_factory("admin@ihomy.local", "admin123")
        auth["http"].request("GET", "/auth/me")
        auth["user"]["role"]  # OWNER/MEMBER/OPS...
    """
    cache: dict[str, dict] = {}

    def _login(email: str, password: str) -> dict:
        if email in cache:
            return cache[email]
        cap = http_base.request("GET", "/auth/captcha").json()["data"]
        body = {
            "email": email,
            "password": password,
            "captchaId": cap["captchaId"],
            "captchaCode": settings.captcha_code,
        }
        r = http_base.request("POST", "/auth/login", json=body).json()
        if r.get("code") != 0:
            raise RuntimeError(f"login failed for {email}: {r.get('message')}")
        data = r["data"]
        client = HttpClient(base_url=settings.api_base_url, token=data["accessToken"])
        entry = {"token": data["accessToken"], "refresh": data["refreshToken"], "user": data["user"], "http": client}
        cache[email] = entry
        logger.info("logged in: %s role=%s familyId=%s", email, data["user"]["role"], data["user"]["familyId"])
        return entry

    yield _login
    for e in cache.values():
        e["http"].close()


@pytest.fixture(scope="session")
def auth(auth_factory):
    """默认 admin(OWNER)登录。"""
    if settings.api_token:
        client = HttpClient(base_url=settings.api_base_url, token=settings.api_token)
        return {"token": settings.api_token, "http": client, "user": {}}
    return auth_factory(settings.api_email, settings.api_password)


@pytest.fixture(scope="session")
def http(auth):
    """带默认 admin token 的 client(兼容旧用例签名)。"""
    return auth["http"]


@pytest.fixture(scope="module")
def second_family_auth(http_base):
    """注册一个临时家庭的 OWNER,用于跨家庭隔离测试。

    注册成功返回 token,session 内复用同一临时家庭。
    """
    email = f"autotest-{uuid.uuid4().hex[:8]}@test.local"
    cap = http_base.request("GET", "/auth/captcha").json()["data"]
    body = {
        "email": email,
        "password": "Test123456",
        "confirmPassword": "Test123456",
        "captchaId": cap["captchaId"],
        "captchaCode": settings.captcha_code,
        "familyName": "autotest-isolated-family",
    }
    r = http_base.request("POST", "/auth/register", json=body).json()
    if r.get("code") != 0:
        raise RuntimeError(f"register failed: {r.get('message')}")
    data = r["data"]
    client = HttpClient(base_url=settings.api_base_url, token=data["accessToken"])
    entry = {"token": data["accessToken"], "user": data["user"], "http": client, "email": email}
    yield entry
    client.close()


# === 数据隔离机制 ===

@pytest.fixture
def cleanup(http):
    """LIFO 清理栈:用例造的数据注册到这里,用例结束(无论成功/失败)自动倒序删除。

    用法:
        resp = http.request("POST", "/blog", json={...})
        blog_id = resp.json()["data"]["id"]
        cleanup.append(("DELETE", f"/blog/{blog_id}"))

    或用 track helper(推荐):
        track(http, cleanup, resp, "DELETE", "/blog/{data.id}")
    """
    stack: list[tuple] = []
    yield stack
    failures = []
    for entry in reversed(stack):
        method = entry[0]
        path = entry[1]
        kwargs = entry[2] if len(entry) > 2 else {}
        try:
            r = http.request(method, path, **kwargs)
            if r.status_code >= 400:
                failures.append(f"{method} {path} -> {r.status_code}")
        except Exception as e:
            failures.append(f"{method} {path} -> {e}")
    if failures:
        logger.warning("cleanup partial failure: %s", "; ".join(failures))


@pytest.fixture
def test_prefix():
    """每次用例执行生成唯一前缀,造数据时带上避免并行/重跑冲突。

    用法:
        title = f"[autotest-{test_prefix}] 测试博客"
    """
    return uuid.uuid4().hex[:8]


@pytest.fixture
def track():
    """提供 track helper,从响应里按 JSONPath 提取 id 自动注册清理。

    用法:
        track(http, cleanup, resp, "DELETE", "/blog/{data.id}")
        track(http, cleanup, resp, "DELETE", "/album/{data.id}/photos/{data.photoIds.0}")
    """
    return _track_cleanup


# === 公共 helper ===

def _resolve_path(template: str, body) -> str:
    """把 {data.id} / {data.items.0.id} 这种简单 JSONPath 替换为响应里的值。"""
    def repl(m: re.Match) -> str:
        path = m.group(1)
        cur = body
        for part in path.split("."):
            if part.isdigit():
                cur = cur[int(part)]
            else:
                cur = cur[part]
        return str(cur)
    return re.sub(r"\{([^}]+)\}", repl, template)


def _track_cleanup(http, cleanup, resp, method: str, path_template: str, **req_kwargs):
    """从响应里提取路径变量,注册到 cleanup 栈。

    path_template 支持简单 JSONPath:{data.id} / {data.blog.id} / {data.items.0.id}
    """
    try:
        body = resp.json()
    except Exception:
        logger.warning("track_cleanup: response is not JSON, skip")
        return
    path = _resolve_path(path_template, body)
    cleanup.append((method, path, req_kwargs))
    logger.info("tracked cleanup: %s %s", method, path)
