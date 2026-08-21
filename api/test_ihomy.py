"""ihomy 核心接口用例(认证/内容/家庭/积分)。

依赖:
- 后端跑在 AUTOTEST_API_BASE_URL(默认 http://localhost:8080/api)
- external.yml 配 app.captcha-fixed-code=qwer
- 种子账号 admin@ihomy.local / admin123(OWNER, familyId=1)

用例原则:每条独立,CRUD 用例自建自清。
"""

import pytest

pytestmark = pytest.mark.api


# ---------- 认证 ----------


def test_captcha(http_base):
    """GET /auth/captcha 返回 captchaId + base64 图片。"""
    r = http_base.request("GET", "/auth/captcha")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["captchaId"]
    assert data["image"].startswith("data:image/png;base64,")


def test_login(auth):
    """auth fixture 已登录,验证响应结构。"""
    u = auth["user"]
    assert u["id"]
    assert u["role"] == "OWNER"
    assert u["familyId"] == 1
    assert isinstance(u["permissions"], list) and len(u["permissions"]) > 0
    assert auth["token"]
    assert auth["refresh"]


def test_auth_me(http):
    """GET /auth/me 返回当前登录用户。"""
    r = http.request("GET", "/auth/me")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["userId"] == 1
    assert data["familyId"] == 1


def test_auth_families(http):
    """GET /auth/families 返回家庭列表,admin 至少有 1 个家庭。"""
    r = http.request("GET", "/auth/families")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list) and len(data) >= 1
    f = data[0]
    assert f["familyId"] == 1
    assert f["role"] == "OWNER"
    assert f["isPrimary"] is True


# ---------- 公开接口 ----------


def test_public_home(http):
    """GET /public/home 返回首页聚合(family/modules/photos/stats)。"""
    r = http.request("GET", "/public/home")
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["family"]["id"] == 1
    assert data["isMember"] is True
    assert isinstance(data["modules"], list)
    assert "photos" in data
    assert "stats" in data


# ---------- 博客 CRUD ----------


def test_blog_crud(http):
    """博客:创建 -> 列表 -> 详情 -> 更新 -> 删除。"""
    # 1) 创建(status=1=PUBLISHED 才进列表)
    payload = {
        "title": "autotest-blog-" + __import__("uuid").uuid4().hex[:8],
        "content": "测试内容",
        "tags": "测试,自动化",
        "category": "autotest",
        "status": 1,
    }
    r = http.request("POST", "/blog", json=payload)
    assert r.status_code == 200
    blog = r.json()["data"]
    bid = blog["id"]
    assert blog["title"] == payload["title"]
    assert blog["familyId"] == 1
    assert blog["status"] == "PUBLISHED"

    try:
        # 2) 列表(按分类过滤)
        r = http.request("GET", "/blog/list", params={"category": "autotest", "size": 5})
        assert r.status_code == 200
        recs = r.json()["data"]["records"]
        assert any(b["id"] == bid for b in recs)

        # 3) 详情
        r = http.request("GET", f"/blog/{bid}")
        assert r.status_code == 200
        assert r.json()["data"]["id"] == bid

        # 4) 更新
        r = http.request("PUT", f"/blog/{bid}", json={"title": "autotest-updated", "content": "改后", "category": "autotest", "status": 1})
        assert r.status_code == 200
        assert r.json()["data"]["title"] == "autotest-updated"

        # 5) 分类列表
        r = http.request("GET", "/blog/categories")
        assert r.status_code == 200
        assert "autotest" in r.json()["data"]
    finally:
        # 6) 清理
        http.request("DELETE", f"/blog/{bid}")


# ---------- 相册 CRUD ----------


def test_album_crud(http):
    """相册:创建 -> 列表 -> 详情 -> 删除。"""
    name = "autotest-album-" + __import__("uuid").uuid4().hex[:8]
    r = http.request("POST", "/album", json={"name": name, "type": "private"})
    assert r.status_code == 200
    album = r.json()["data"]
    aid = album["id"]
    assert album["name"] == name

    try:
        # 列表
        r = http.request("GET", "/album/list")
        assert r.status_code == 200
        assert any(a["id"] == aid for a in r.json()["data"])

        # 详情(返回 {album: {...}, photos: [...]})
        r = http.request("GET", f"/album/{aid}")
        assert r.status_code == 200
        assert r.json()["data"]["album"]["id"] == aid
        assert isinstance(r.json()["data"]["photos"], list)
    finally:
        http.request("DELETE", f"/album/{aid}")


# ---------- 点赞 ----------


def test_like_toggle(http):
    """点赞:对博客 toggle on -> state=liked -> toggle off -> state=unliked。"""
    # 先建一篇博客作为点赞目标
    r = http.request("POST", "/blog", json={"title": "like-target", "category": "autotest", "status": 1})
    bid = r.json()["data"]["id"]
    try:
        # toggle on
        r = http.request("POST", "/like/toggle", json={"contentType": "blog", "contentId": bid})
        assert r.status_code == 200
        assert r.json()["data"]["liked"] is True

        # state
        r = http.request("GET", "/like/state", params={"contentType": "blog", "contentId": bid})
        assert r.status_code == 200
        assert r.json()["data"]["liked"] is True

        # toggle off
        r = http.request("POST", "/like/toggle", json={"contentType": "blog", "contentId": bid})
        assert r.json()["data"]["liked"] is False
    finally:
        http.request("DELETE", f"/blog/{bid}")


# ---------- 评论 ----------


def test_comment_crud(http):
    """评论:对博客发表 -> 列表 -> 删除。"""
    r = http.request("POST", "/blog", json={"title": "comment-target", "category": "autotest", "status": 1})
    bid = r.json()["data"]["id"]
    try:
        # 发表评论
        r = http.request("POST", "/comment", json={"contentType": "blog", "contentId": bid, "content": "autotest comment"})
        assert r.status_code == 200
        cid = r.json()["data"]["id"]
        assert r.json()["data"]["content"] == "autotest comment"

        # 列表
        r = http.request("GET", "/comment/list", params={"contentType": "blog", "contentId": bid})
        assert r.status_code == 200
        assert any(c["id"] == cid for c in r.json()["data"])

        # 删除
        r = http.request("DELETE", f"/comment/{cid}")
        assert r.status_code == 200
        r = http.request("GET", "/comment/list", params={"contentType": "blog", "contentId": bid})
        assert not any(c["id"] == cid for c in r.json()["data"])
    finally:
        http.request("DELETE", f"/blog/{bid}")


# ---------- 通知 ----------


def test_notification_list(http):
    """GET /notification/list + /unread-count 结构校验。"""
    r = http.request("GET", "/notification/list")
    assert r.status_code == 200
    data = r.json()["data"]
    assert isinstance(data, list)

    r = http.request("GET", "/notification/unread-count")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], int) or r.json()["data"] is None


# ---------- 积分 ----------


def test_points_stats(http):
    """GET /points/stats 返回积分概览。"""
    r = http.request("GET", "/points/stats")
    assert r.status_code == 200
    data = r.json()["data"]
    assert "balance" in data
    assert "checkedToday" in data
    assert "streak" in data


def test_points_products(http):
    """GET /points/products 返回家庭商品列表。"""
    r = http.request("GET", "/points/products")
    assert r.status_code == 200
    assert isinstance(r.json()["data"], list)
