import pytest

from common.config import settings
from ui.pages.login_page import LoginPage

pytestmark = [pytest.mark.ui]


def test_login_redirects(page):
    LoginPage(page).goto(settings.ui_base_url).login("admin", "admin")
    assert "/login" not in page.url
