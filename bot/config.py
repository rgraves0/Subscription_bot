# bot/config.py
import os
import logging

# Logger setup (temporary for config.py, will use bot.logger later)
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

class Config:
    # Load from environment variables with defaults
    APP_ID = os.getenv("APP_ID", "your_api_id")
    API_HASH = os.getenv("API_HASH", "your_api_hash")
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "your_bot_token")
    DOWNLOAD_BASE_DIR = os.getenv("DOWNLOAD_BASE_DIR", "/app/downloads")
    WORK_DIR = os.getenv("WORK_DIR", "./")
    ADMIN_ID = int(os.getenv("ADMIN_ID", "1281749717"))  # Default to your ID if not set
    DATABASE_URL = os.getenv("DATABASE_URL", "postgres://user:password@host:port/dbname")
    AUTH_CHAT = os.getenv("AUTH_CHAT", "").split(",") if os.getenv("AUTH_CHAT") else []
    AUTH_USERS = os.getenv("AUTH_USERS", "").split(",") if os.getenv("AUTH_USERS") else ""
    ADMINS = [int(x) for x in os.getenv("ADMINS", "").split(",") if x] if os.getenv("ADMINS") else []
    IS_BOT_PUBLIC = os.getenv("IS_BOT_PUBLIC", "False")
    ANIT_SPAM_MODE = os.getenv("ANIT_SPAM_MODE", "True")
    MENTION_USERS = os.getenv("MENTION_USERS", "True")
    TIDAL_TRACK_FORMAT = os.getenv("TIDAL_TRACK_FORMAT", "{TrackNumber} - {ArtistName} - {TrackTitle}{ExplicitFlag}")
    QOBUZ_TRACK_FORMAT = os.getenv("QOBUZ_TRACK_FORMAT", "{TrackNumber} - {ArtistName} - {TrackTitle}")
    KKBOX_EMAIL = os.getenv("KKBOX_EMAIL", "")
    KKBOX_KEY = os.getenv("KKBOX_KEY", "")
    KKBOX_PASSWORD = os.getenv("KKBOX_PASSWORD", "")
    QOBUZ_EMAIL = os.getenv("QOBUZ_EMAIL", "")
    QOBUZ_PASSWORD = os.getenv("QOBUZ_PASSWORD", "")
    DEEZER_EMAIL = os.getenv("DEEZER_EMAIL", "")
    DEEZER_PASSWORD = os.getenv("DEEZER_PASSWORD", "")
    DEEZER_ARL = os.getenv("DEEZER_ARL", "")
    DEEZER_BF_SECRET = os.getenv("DEEZER_BF_SECRET", "")
    DEEZER_TRACK_URL_KEY = os.getenv("DEEZER_TRACK_URL_KEY", "")
    SPOTIFY_EMAIL = os.getenv("SPOTIFY_EMAIL", "")
    SPOTIFY_PASS = os.getenv("SPOTIFY_PASS", "")
    BOT_LANGUAGE = os.getenv("BOT_LANGUAGE", "en")

    def __init__(self):
        # Check for admin IDs and log appropriately
        if self.ADMIN_ID == 0 and not any(self.ADMINS):  # Only warn if ADMIN_ID is 0 and ADMINS is empty
            LOGGER.warning("NO ADMIN USER IDS FOUND")
        else:
            if self.ADMIN_ID != 0:
                LOGGER.info(f"Admin ID set: {self.ADMIN_ID}")
            if self.ADMINS:
                LOGGER.info(f"Additional Admins: {self.ADMINS}")
