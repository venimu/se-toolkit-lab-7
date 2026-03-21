"""Configuration loading from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class BotSettings(BaseSettings):
    """Bot configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env.bot.secret",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Telegram bot token
    bot_token: str

    # LMS API configuration
    lms_api_base_url: str
    lms_api_key: str

    # LLM API configuration
    llm_api_model: str = "coder-model"
    llm_api_key: str
    llm_api_base_url: str


def load_config() -> BotSettings:
    """Load and return bot configuration."""
    return BotSettings()
