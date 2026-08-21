class LoginPage:
    def __init__(self, page):
        self.page = page

    def goto(self, base_url: str) -> "LoginPage":
        self.page.goto(f"{base_url}/login")
        self.page.wait_for_selector(".login-card")
        return self

    def login(self, username: str, password: str) -> None:
        self.page.fill('input[placeholder="admin"]', username)
        self.page.fill('input[type="password"]', password)
        self.page.click('button:has-text("登录")')
        self.page.wait_for_url("**/dashboard", timeout=10000)
