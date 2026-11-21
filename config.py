"""All settings in one place.

Values come from environment variables, usually through a `.env` file
(see `.env.example`). Every other module imports `settings` from here
instead of reading the environment itself.
"""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class ConfigError(RuntimeError):
    """A required setting is missing."""


def _optional(name: str) -> str | None:
    value = os.getenv(name, "").strip()
    return value or None


def _required(name: str) -> str:
    value = _optional(name)
    if value is None:
        raise ConfigError(
            f"Missing {name}. Copy .env.example to .env and fill in your keys."
        )
    return value


@dataclass(frozen=True)
class Settings:
    # Language model
    gemini_api_key: str
    gemini_model: str  # orchestrator and responses
    gemini_helper_model: str  # smaller tasks: device matching, email drafts

    # Optional services (each tool explains what is missing when it is used)
    tavily_api_key: str | None
    deepgram_api_key: str | None

    # Files
    database_path: Path
    google_credentials_path: Path
    google_token_path: Path
    browser_binary: str | None  # None = the default Chrome


def load_settings() -> Settings:
    return Settings(
        gemini_api_key=_required("GEMINI_API_KEY"),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
        gemini_helper_model=os.getenv("GEMINI_HELPER_MODEL", "gemini-3.5-flash-lite"),
        tavily_api_key=_optional("TAVILY_API_KEY"),
        deepgram_api_key=_optional("DEEPGRAM_API_KEY"),
        database_path=Path(os.getenv("DATABASE_PATH", "devices.db")),
        google_credentials_path=Path(
            os.getenv("GOOGLE_CREDENTIALS_PATH", "secrets/credentials.json")
        ),
        google_token_path=Path(os.getenv("GOOGLE_TOKEN_PATH", "secrets/token.json")),
        browser_binary=_optional("BROWSER_BINARY"),
    )


def require(value: str | None, name: str, feature: str) -> str:
    """Return an optional setting, or explain which feature needs it."""
    if value is None:
        raise ConfigError(f"{feature} needs {name}. Add it to your .env file.")
    return value


settings = load_settings()
