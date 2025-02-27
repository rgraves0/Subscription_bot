# bot/config.py
import os

class Config:
    APP_ID = "your_api_id"
    API_HASH = "your_api_hash"
    TG_BOT_TOKEN = "your_bot_token"
    DOWNLOAD_BASE_DIR = "/app/downloads"
    WORK_DIR = "./"
    ADMIN_ID = 1281749717  # Your Telegram ID
    DATABASE_URL = "postgres://user:password@host:port/dbname"
    AUTH_CHAT = []
    AUTH_USERS = ""
    ADMINS = []
    IS_BOT_PUBLIC = "False"
    ANIT_SPAM_MODE = "True"
    MENTION_USERS = "True"
    TIDAL_TRACK_FORMAT = "{TrackNumber} - {ArtistName} - {TrackTitle}{ExplicitFlag}"
    QOBUZ_TRACK_FORMAT = "{TrackNumber} - {ArtistName} - {TrackTitle}"
    KKBOX_EMAIL = ""
    KKBOX_KEY = ""
    KKBOX_PASSWORD = ""
    QOBUZ_EMAIL = ""
    QOBUZ_PASSWORD = ""
    DEEZER_EMAIL = ""
    DEEZER_PASSWORD = ""
    DEEZER_ARL = ""
    DEEZER_BF_SECRET = ""
    DEEZER_TRACK_URL_KEY = ""
    SPOTIFY_EMAIL = ""
    SPOTIFY_PASS = ""
    BOT_LANGUAGE = "en"
