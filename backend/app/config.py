from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    RAPIDAPI_KEY: str = ""
    RAPIDAPI_YAHOO_FINANCE_HOST: str = "yahoo-finance15.p.rapidapi.com"

    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    REDDIT_USER_AGENT: str = "TechFin/1.0"

    ALPHAVANTAGE_API_KEY: str = ""


settings = Settings()  # type: ignore[call-arg]
