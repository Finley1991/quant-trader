from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Tushare
    TUSHARE_TOKEN: str = ""

    # DingTalk
    DINGTALK_WEBHOOK: str = ""
    DINGTALK_SECRET: str = ""

    # Email (phase 2)
    EMAIL_SMTP_HOST: str = ""
    EMAIL_SMTP_PORT: int = 587
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""

    # Database
    DATABASE_URL: str = "sqlite:///./quant_trader.db"

    # Application
    APP_NAME: str = "Quant Trader"
    DEBUG: bool = True

    class Config:
        env_file = ".env"

settings = Settings()
