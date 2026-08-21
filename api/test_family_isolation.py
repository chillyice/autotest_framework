"""ihomy 家庭隔离用例。

核心场景:
- 用户 A(family 1)发的博客,用户 B(family 2)不能见/不能点赞/不能评论
- 跨家庭访问返回 code=404(NOT_FOUND,防枚举)

实现:second_family_auth fixture(在 conftest.py)注册临时家庭,
用它的 OWNER 去访问 admin(family 1)的博客,预期 404。
"""

import pytest

pytestmark = pytest.mark.api


def test_two_families_are_different(http, second_family_auth):
    """admin(family 1)和 second_family(family X)familyId 不同。"""
    admin_fid = http.request("GET", "/auth/me").json()["data"]["familyId"]
    second_fid = second_family_auth["user"]["familyId"]
    assert admin_fid == 1
    assert second_fid != 1
    assert second_fid is not None


def test_cross_family_blog_returns_404(http, second_family_auth):
    """admin 发的博客,second_family 用户访问返回 code=404。"""
    # admin 建一篇博客(默认 visibility=FAMILY)
    r = http.request("POST", "/blog", json={"title": "cross-family-target", "category": "autotest", "status": 1})
    bid = r.json()["data"]["id"]
    try:
        # second_family 用户尝试访问 → 404
        r = second_family_auth["http"].request("GET", f"/blog/{bid}")
        assert r.json()["code"] == 404
    finally:
        http.request("DELETE", f"/blog/{bid}")


def test_cross_family_like_returns_404(http, second_family_auth):
    """second_family 用户对 admin 的博客点赞 → 404。"""
    r = http.request("POST", "/blog", json={"title": "like-cross-family", "category": "autotest", "status": 1})
    bid = r.json()["data"]["id"]
    try:
        r = second_family_auth["http"].request(
            "POST", "/like/toggle", json={"contentType": "blog", "contentId": bid}
        )
        assert r.json()["code"] == 404
    finally:
        http.request("DELETE", f"/blog/{bid}")


def test_cross_family_comment_returns_404(http, second_family_auth):
    """second_family 用户对 admin 的博客评论 → 404。"""
    r = http.request("POST", "/blog", json={"title": "comment-cross-family", "category": "autotest", "status": 1})
    bid = r.json()["data"]["id"]
    try:
        r = second_family_auth["http"].request(
            "POST", "/comment",
            json={"contentType": "blog", "contentId": bid, "content": "should fail"},
        )
        assert r.json()["code"] == 404
    finally:
        http.request("DELETE", f"/blog/{bid}")


def test_cross_family_blog_list_excludes_other_family(second_family_auth):
    """second_family 用户看 /blog/list,看不到 admin 家庭的博客。"""
    # admin 建博客
    # (这里用 second_family 自己的列表验证,不依赖 admin 建数据)
    r = second_family_auth["http"].request("GET", "/blog/list", params={"size": 100})
    assert r.json()["code"] == 0
    recs = r.json()["data"]["records"]
    # second_family 是新注册的家庭,没有任何博客(除非之前用例泄漏)
    # 关键断言:列表里所有博客的 familyId 都属于 second_family
    second_fid = second_family_auth["user"]["familyId"]
    for b in recs:
        assert b["familyId"] == second_fid
