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
    pagination_size: int
    description_template: str
    log_level: str

def _ids(value: str) -> frozenset[int]:
    return frozenset(int(x.strip()) for x in value.split(',') if x.strip())

def _optional_int(value: str) -> int | None:
    return int(value) if value.strip() else None

def load_settings() -> Settings:
    token = os.getenv('BOT_TOKEN', '').strip()
    if not token:
        raise RuntimeError('BOT_TOKEN .env faylida berilmagan.')
    return Settings(
        bot_token=token,
        database_url=os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///./anime_bot.db'),
        admin_ids=_ids(os.getenv('ADMIN_IDS', '')),
        owner_id=_optional_int(os.getenv('OWNER_ID', '')),
        channel_id=_optional_int(os.getenv('CHANNEL_ID', '')),
        log_channel_id=_optional_int(os.getenv('LOG_CHANNEL_ID', '')),
        pagination_size=max(1, min(50, int(os.getenv('PAGINATION_SIZE', '10')))),
        description_template=os.getenv('DESCRIPTION_TEMPLATE', '🎬 {anime_name}\n📺 {episode}-qism'),
        log_level=os.getenv('LOG_LEVEL', 'INFO'),
    )
