from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="AUTOTEST_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 被测系统地址(默认 ihomy 本地开发)
    api_base_url: str = "http://localhost:8080/api"
    ui_base_url: str = "http://localhost:5173"
    headless: bool = True

    # ihomy 登录凭证(session 级 fixture 用)
    api_email: str = "admin@ihomy.local"
    api_password: str = "admin123"
    # 开发环境固定验证码(external.yml app.captcha-fixed-code=qwer)
    captcha_code: str = "qwer"

    # 兼容旧字段:若直接提供 token 则 auth fixture 跳过登录
    api_token: str | None = None


settings = Settings()
