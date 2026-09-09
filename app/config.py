import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    admin_ids: frozenset[int]
    owner_id: int | None
    channel_id: int | None
    log_channel_id: int | None
    mandatory_channels: tuple[str, ...]
    pagination_size: int
    description_template: str
    log_level: str
    webapp_url: str | None


def _ids(value: str) -> frozenset[int]:
    return frozenset(int(x.strip()) for x in value.split(',') if x.strip())


def _optional_int(value: str) -> int | None:
    return int(value) if value.strip() else None


def _int_env(name: str, default: int, low: int, high: int) -> int:
    try:
        return max(low, min(high, int((os.getenv(name) or str(default)).strip())))
    except (TypeError, ValueError):
        return default


def load_settings() -> Settings:
    token = (os.getenv('BOT_TOKEN') or '').strip()
    if not token:
        raise RuntimeError('BOT_TOKEN .env faylida berilmagan.')
    mandatory = tuple(x.strip() for x in (os.getenv('MANDATORY_CHANNELS') or '').split(',') if x.strip())
    return Settings(
        bot_token=token,
        database_url=(os.getenv('DATABASE_URL') or 'sqlite+aiosqlite:///./anime_bot.db').strip(),
        admin_ids=_ids(os.getenv('ADMIN_IDS') or ''),
        owner_id=_optional_int(os.getenv('OWNER_ID') or ''),
        channel_id=_optional_int(os.getenv('CHANNEL_ID') or ''),
        log_channel_id=_optional_int(os.getenv('LOG_CHANNEL_ID') or ''),
        mandatory_channels=mandatory,
        pagination_size=_int_env('PAGINATION_SIZE', 10, 1, 50),
        description_template=(os.getenv('DESCRIPTION_TEMPLATE') or '🎬 {anime_name}\n📺 {episode}-qism'),
        log_level=(os.getenv('LOG_LEVEL') or 'INFO').upper(),
        webapp_url=(os.getenv('WEBAPP_URL') or '').strip() or None,
    )
