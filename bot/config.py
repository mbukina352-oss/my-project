"""Настройки бота. Всё берётся из переменных окружения (файл .env)."""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def _env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _ids(value: str) -> set[int]:
    return {int(x) for x in value.replace(" ", "").split(",") if x}


@dataclass(frozen=True)
class Agent:
    """Данные агента, которые ставятся на каждый PDF."""
    name: str = _env("AGENT_NAME")
    phone: str = _env("AGENT_PHONE")
    email: str = _env("AGENT_EMAIL")
    agency: str = _env("AGENT_AGENCY")
    telegram: str = _env("AGENT_TELEGRAM")
    logo_path: str = _env("AGENT_LOGO", "assets/logo.png")

    @property
    def logo(self) -> Path | None:
        p = Path(self.logo_path)
        return p if self.logo_path and p.is_file() else None


@dataclass(frozen=True)
class TrendAgent:
    login: str = _env("TA_LOGIN")
    password: str = _env("TA_PASSWORD")
    city: str = _env("TA_CITY", "msk")
    login_url: str = _env("TA_LOGIN_URL", "https://sso.trendagent.ru/login")
    # {query} подставляется в URL поиска по названию ЖК
    search_url: str = _env("TA_SEARCH_URL", "https://msk.trendagent.ru/objects/list/?search={query}")
    phone_selector: str = _env("TA_PHONE_SELECTOR", "input[name=phone], input[type=tel], input[name=login]")
    password_selector: str = _env("TA_PASSWORD_SELECTOR", "input[type=password]")
    submit_selector: str = _env("TA_SUBMIT_SELECTOR", "button[type=submit]")
    state_file: str = _env("TA_STATE_FILE", "data/trendagent_state.json")
    headless: bool = _env("TA_HEADLESS", "1") != "0"


@dataclass(frozen=True)
class Settings:
    bot_token: str = _env("BOT_TOKEN")
    allowed_users: set[int] = field(default_factory=lambda: _ids(_env("ALLOWED_USER_IDS")))
    price_tolerance: float = float(_env("PRICE_TOLERANCE", "0.10"))
    area_tolerance: float = float(_env("AREA_TOLERANCE", "0.10"))
    max_results: int = int(_env("MAX_RESULTS", "3"))
    font_path: str = _env("FONT_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    font_bold_path: str = _env("FONT_BOLD_PATH", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    agent: Agent = field(default_factory=Agent)
    trendagent: TrendAgent = field(default_factory=TrendAgent)


settings = Settings()
