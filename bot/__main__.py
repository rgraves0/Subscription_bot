import os
import sys
import asyncio
from pyrogram import Client
from bot import Config, LOGGER
from bot.helpers.qobuz.handler import qobuz
from bot.helpers.tidal_func.events import checkAPITidal
from bot.helpers.tidal_func.settings import TIDAL_SETTINGS, TIDAL_TOKEN

plugins = dict(root="bot/modules")

async def loadConfigs():
    # TIDAL
    TIDAL_SETTINGS.read()
    TIDAL_TOKEN.read("./tidal-dl.token.json")
    await checkAPITidal()
    LOGGER.info('Loaded TIDAL Successfully')

async def download_url(url):
    LOGGER.info(f"Attempting to download: {url}")
    if "tidal" in url.lower():
        return "Tidal download completed (placeholder)"
    elif "qobuz" in url.lower():
        await qobuz.login()  # Assuming qobuz.login() is async
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

async def main():
    if not os.path.isdir(Config.DOWNLOAD_BASE_DIR):
        os.makedirs(Config.DOWNLOAD_BASE_DIR)

    app = Bot()

    if len(sys.argv) > 1:  # Command-line URL download mode
        url = sys.argv[1]
        await app.start()
        try:
            result = await download_url(url)
            print(result)
        finally:
            await app.stop()
    else:  # Normal bot mode
        await app.start()
        try:
            await app.idle()
        finally:
            await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
