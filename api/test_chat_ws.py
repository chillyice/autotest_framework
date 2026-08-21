"""ihomy 聊天室 WebSocket 用例。

覆盖:
- 握手成功(token 有效)
- 握手失败(无 token / 假 token)
- 发送消息 -> 自己收到广播
- 同家庭另一用户收到广播
- 跨家庭用户收不到广播
- 消息落库(/chat/history 能查到)
"""

import uuid

import pytest

from common.config import settings
from common.ws_client import WsClient

pytestmark = pytest.mark.api


def _connect(token: str):
    """同步建连,返回 WsClient(已 connect)。失败抛异常。"""
    client = WsClient(settings.api_base_url, token)
    return client.connect()


def _close(client):
    if client:
        client.close()


# ---------- 握手 ----------


def test_ws_handshake_with_valid_token(auth):
    """有效 token 能握手成功。"""
    client = _connect(auth["token"])
    try:
        # websockets 17:连接成功即 ws 非空,send 不抛即已建立
        assert client.ws is not None
        client.send("ping-test")  # 能发即连接有效
    finally:
        _close(client)


def test_ws_handshake_without_token_fails():
    """无 token 握手被拒绝(服务端返回 HTTP 200 非 ws 升级,websockets 抛异常)。"""
    with pytest.raises(Exception):
        _connect("")


def test_ws_handshake_with_invalid_token_fails():
    """假 token 握手失败。"""
    with pytest.raises(Exception):
        _connect("fake.token.here")


# ---------- 消息收发 ----------


def test_ws_send_and_receive_broadcast(auth):
    """发送消息 -> 自己收到广播(envelope type=message)。"""
    client = _connect(auth["token"])
    try:
        content = f"autotest-ws-{uuid.uuid4().hex[:8]}"
        client.drain()

        client.send(content)
        msg = client.recv(timeout=3.0)

        assert msg["type"] == "message"
        assert msg["data"]["content"] == content
        assert msg["data"]["senderId"] == auth["user"]["id"]
        assert msg["data"]["familyId"] == auth["user"]["familyId"]
    finally:
        _close(client)


def test_ws_broadcast_to_same_family(auth_factory):
    """同家庭两个连接,一个发消息另一个收到广播(admin 开两个连接,同 familyId=1)。"""
    c1 = _connect(auth_factory("admin@ihomy.local", "admin123")["token"])
    c2 = _connect(auth_factory("admin@ihomy.local", "admin123")["token"])
    try:
        c1.drain()
        c2.drain()

        content = f"broadcast-{uuid.uuid4().hex[:8]}"
        c1.send(content)

        # c2 应收到
        msg = c2.recv(timeout=3.0)
        assert msg["type"] == "message"
        assert msg["data"]["content"] == content

        # c1 自己也应收到
        msg = c1.recv(timeout=3.0)
        assert msg["data"]["content"] == content
    finally:
        _close(c1)
        _close(c2)


def test_ws_no_cross_family_leak(auth, second_family_auth):
    """跨家庭广播不泄漏:admin(family 1)发消息,second_family(family X)收不到。"""
    c_other = _connect(second_family_auth["token"])
    try:
        c_other.drain()

        c_admin = _connect(auth["token"])
        try:
            c_admin.drain()
            content = f"iso-{uuid.uuid4().hex[:8]}"
            c_admin.send(content)

            # admin 自己能收到
            msg = c_admin.recv(timeout=2.0)
            assert msg["data"]["content"] == content

            # second_family 不应收到(等 0.8s 确认无消息)
            with pytest.raises(TimeoutError):
                c_other.recv(timeout=0.8)
        finally:
            _close(c_admin)
    finally:
        _close(c_other)


# ---------- 消息落库 ----------


def test_ws_message_persisted(http, auth):
    """发送的消息落库,/chat/history 能查到。"""
    content = f"persist-{uuid.uuid4().hex[:8]}"
    client = _connect(auth["token"])
    try:
        client.drain()
        client.send(content)
        # 等自己收到确认落库
        client.recv(timeout=3.0)
    finally:
        _close(client)

    r = http.request("GET", "/chat/history", params={"limit": 50})
    assert r.json()["code"] == 0
    recs = r.json()["data"]
    assert any(m["content"] == content for m in recs), f"消息 {content} 未落库"


# ---------- 边界 ----------


def test_ws_empty_content_disconnects(auth):
    """空内容触发 POLICY_VIOLATION 关闭连接。"""
    client = _connect(auth["token"])
    try:
        client.drain()
        client.send("")
        # 再 recv 会抛 ConnectionClosed
        with pytest.raises(Exception):
            client.recv(timeout=2.0)
    finally:
        try:
            _close(client)
        except Exception:
            pass
