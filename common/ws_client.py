"""ihomy 聊天室 WebSocket 客户端封装。

端点:ws://{host}/api/ws/chat?token={accessToken}
协议:发送 {"content":"xxx"} -> 广播 {"type":"message","data":{id,familyId,senderId,content,createdAt}}

设计:每个 WsClient 持有独立事件循环(线程内单循环),所有 async 操作走该循环。
"""

import asyncio
import json
import threading
from urllib.parse import urlparse

import websockets

from common.logger import logger


class WsClient:
    """单连接 WebSocket 客户端。同步接口,内部自管事件循环。"""

    def __init__(self, base_url: str, token: str):
        u = urlparse(base_url)
        scheme = "wss" if u.scheme == "https" else "ws"
        self.ws_url = f"{scheme}://{u.netloc}/api/ws/chat?token={token}"
        self.ws = None
        self._loop = asyncio.new_event_loop()

    def connect(self):
        self._run(self._connect())
        return self

    async def _connect(self):
        self.ws = await websockets.connect(self.ws_url)
        logger.info("ws connected: %s", self.ws_url.split("token=")[0])

    def send(self, content: str):
        self._run(self.ws.send(json.dumps({"content": content})))

    def recv(self, timeout: float = 3.0):
        return self._run(asyncio.wait_for(self._recv_json(), timeout=timeout))

    async def _recv_json(self):
        raw = await self.ws.recv()
        return json.loads(raw)

    def drain(self, timeout: float = 0.3):
        """排空已收但未读的消息。返回排掉的数量。"""
        async def _drain():
            n = 0
            try:
                while True:
                    await asyncio.wait_for(self._recv_json(), timeout=timeout)
                    n += 1
            except asyncio.TimeoutError:
                return n
        return self._run(_drain())

    def close(self):
        if self.ws:
            try:
                self._run(self.ws.close())
            except Exception:
                pass
            logger.info("ws closed")
        self._loop.close()

    def _run(self, coro):
        return self._loop.run_until_complete(coro)
