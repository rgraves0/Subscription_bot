# bot/config.py
import os

class Config:
    APP_ID = int(os.getenv("APP_ID", "0"))  # Telegram App ID from my.telegram.org
    API_HASH = os.getenv("API_HASH", "")     # Telegram API Hash from my.telegram.org
    TG_BOT_TOKEN = os.getenv("TG_BOT_TOKEN", "")
    WORK_DIR = "./"
    DOWNLOAD_BASE_DIR = "./downloads"
    QOBUZ_EMAIL = os.getenv("QOBUZ_EMAIL", "")
    QOBUZ_PASSWORD = os.getenv("QOBUZ_PASSWORD", "")
    DEEZER_EMAIL = os.getenv("DEEZER_EMAIL", "")
    DEEZER_PASSWORD = os.getenv("DEEZER_PASSWORD", "")
    DEEZER_BF_SECRET = os.getenv("DEEZER_BF_SECRET", "")
    DEEZER_TRACK_URL_KEY = os.getenv("DEEZER_TRACK_URL_KEY", "")
    DEEZER_ARL = os.getenv("DEEZER_ARL", "")
    KKBOX_EMAIL = os.getenv("KKBOX_EMAIL", "")
    KKBOX_KEY = os.getenv("KKBOX_KEY", "")
    KKBOX_PASSWORD = os.getenv("KKBOX_PASSWORD", "")
    SPOTIFY_EMAIL = os.getenv("SPOTIFY_EMAIL", "")
    SPOTIFY_PASS = os.getenv("SPOTIFY_PASS", "")
    ANIT_SPAM_MODE = os.getenv("ANIT_SPAM_MODE", "False")