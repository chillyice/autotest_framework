import requests

from common.logger import logger


class HttpClient:
    """requests.Session 封装:带 token + traceId 日志。

    ponytail: 不做 401 自动刷新(access token 2h 够 session 用);
    不做重试(用例应显式处理);需要时再加。
    """

    def __init__(self, base_url: str, token: str | None = None):
        self.session = requests.Session()
        self.base_url = base_url.rstrip("/")
        self.token = token
        if token:
            self.session.headers["Authorization"] = f"Bearer {token}"

    def request(self, method: str, path: str, **kwargs):
        url = path if path.startswith("http") else f"{self.base_url}/{path.lstrip('/')}"
        r = self.session.request(method, url, **kwargs)
        trace = r.headers.get("X-Trace-Id", "-")
        logger.info("%s %s -> %s trace=%s", method, path, r.status_code, trace)
        return r

    def close(self):
        self.session.close()


# ponytail: 只暴露 request,加 get/post 别名当真有重复样板时再说
