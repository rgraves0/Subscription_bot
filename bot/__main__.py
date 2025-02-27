import os
import sys
from pyrogram import Client
from bot import Config, LOGGER
from bot.helpers.utils.auth_check import get_chats
from bot.helpers.qobuz.handler import qobuz
from bot.helpers.deezer.handler import deezerdl
from bot.helpers.kkbox.kkbox_helper import kkbox
from bot.helpers.spotify.handler import spotify_dl
from bot.helpers.database.postgres_impl import set_db
from bot.helpers.tidal_func.events import checkAPITidal
from bot.helpers.tidal_func.settings import TIDAL_SETTINGS, TIDAL_TOKEN

plugins = dict(
    root="bot/modules"
)

async def loadConfigs():
    # TIDAL
    TIDAL_SETTINGS.read()
    TIDAL_TOKEN.read("./tidal-dl.token.json")
    await checkAPITidal()
    LOGGER.info('Loaded TIDAL Successfully')
    # KKBOX
    if not "" in {Config.KKBOX_EMAIL, Config.KKBOX_KEY, Config.KKBOX_PASSWORD}:
        await kkbox.login()
        LOGGER.info('Loaded KKBOX Successfully')
    else:
        set_db.set_variable("KKBOX_AUTH", False, False, None)
    # QOBUZ
    if not "" in {Config.QOBUZ_EMAIL, Config.QOBUZ_PASSWORD}:
        await qobuz.login()
    else:
        set_db.set_variable("QOBUZ_AUTH", False, False, None)
    # DEEZER
    if not "" in {Config.DEEZER_EMAIL, Config.DEEZER_PASSWORD}:
        if Config.DEEZER_BF_SECRET == "":
            LOGGER.warning("Deezer BF Secret not provided. Get it from OrpheusDL Telegram Chat.")
            exit(1)
        if Config.DEEZER_TRACK_URL_KEY == "":
            LOGGER.warning("Deezer Track URL Key not provided. Get it from OrpheusDL Telegram Chat.")
            exit(1)
        await deezerdl.login()
    elif Config.DEEZER_ARL != "":
        await deezerdl.login(True)
    else:
        set_db.set_variable("DEEZER_AUTH", False, False, None)
    if not "" in {Config.SPOTIFY_EMAIL, Config.SPOTIFY_PASS}:
        await spotify_dl.login()
        set_db.set_variable("SPOTIFY_AUTH", True, False, None)
    else:
        set_db.set_variable("SPOTIFY_AUTH", False, False, None)

async def download_url(url):
    # Placeholder for download logic
    # This should call the appropriate handler based on URL (Tidal, Qobuz, etc.)
    LOGGER.info(f"Attempting to download: {url}")
    if "tidal" in url.lower():
        # Add Tidal download logic here
        return "Tidal download completed (placeholder)"
    elif "qobuz" in url.lower():
        # Add Qobuz download logic here
        return "Qobuz download completed (placeholder)"
    else:
        return "Unsupported URL format"

class Bot(Client):
    def __init__(self):
        super().__init__(
            "AIO-Music-Bot",
            api_id=Config.APP_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.TG_BOT_TOKEN,
            plugins=plugins,
            workdir=Config.WORK_DIR
        )

    async def start(self):
        await super().start()
        await loadConfigs()
        LOGGER.info("❤ MUSIC HELPER BOT BETA v0.30 STARTED SUCCESSFULLY ❤")

    async def stop(self, *args):
        await super().stop()
        LOGGER.info('Bot Exited Successfully ! Bye..........')

if __name__ == "__main__":
    if not os.path.isdir(Config.DOWNLOAD_BASE_DIR):
        os.makedirs(Config.DOWNLOAD_BASE_DIR)
    
    # Check if URL is provided as command-line argument
    if len(sys.argv) > 1:
        url = sys.argv[1]
        app = Bot()
        with app:
            result = app.run(download_url(url))
            print(result)
    else:
        app = Bot()
        app.run()