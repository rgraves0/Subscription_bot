import os
import sys
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import Config, LOGGER
from bot.helpers.tidal_func.settings import TIDAL_SETTINGS, TIDAL_TOKEN
from bot.helpers.database.postgres_impl import set_db
import tidal_dl  # Tidal-dl library

plugins = dict(root="bot/modules")

# Tidal Authentication Function
async def tidal_authenticate():
    try:
        # tidal-dl ကို အသုံးပြုပြီး login
        tidal = tidal_dl.TidalDL()
        tidal.login()  # This prompts for credentials in terminal; we'll adapt for Telegram
        TIDAL_SETTINGS.read()
        TIDAL_TOKEN.read("./tidal-dl.token.json")
        set_db.set_variable("TIDAL_AUTH", True, False, None)  # Store auth state in DB
        LOGGER.info("Tidal authenticated successfully")
        return True
    except Exception as e:
        LOGGER.error(f"Tidal authentication failed: {e}")
        return False

async def loadConfigs():
    tidal_auth = set_db.get_variable("TIDAL_AUTH")
    if not tidal_auth or not tidal_auth[0]:
        LOGGER.info("Tidal not authenticated yet. Use /tidal_auth to authenticate.")
    else:
        TIDAL_SETTINGS.read()
        TIDAL_TOKEN.read("./tidal-dl.token.json")
        LOGGER.info("Loaded TIDAL Successfully")

async def download_url(url):
    LOGGER.info(f"Attempting to download: {url}")
    tidal_auth = set_db.get_variable("TIDAL_AUTH")
    if "tidal" in url.lower():
        if tidal_auth and tidal_auth[0]:
            tidal = tidal_dl.TidalDL()
            tidal.download(url)  # Assuming tidal-dl has this method
            return "Tidal download completed"
        else:
            return "Tidal not authenticated. Use /tidal_auth first."
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

# Admin check filter
def admin_only(func):
    async def wrapper(client, message: Message):
        if message.from_user.id == Config.ADMIN_ID:  # Define ADMIN_ID in config.py
            await func(client, message)
        else:
            await message.reply("This command is for admins only!")
    return wrapper

# Tidal Auth Command
@Bot.on_message(filters.command("tidal_auth") & filters.private)
@admin_only
async def tidal_auth_command(client: Bot, message: Message):
    await message.reply("Please send your Tidal username and password in the format:\n`username:password`")
    # Wait for the next message from the same user
    response = await client.listen.Message(filters.user(message.from_user.id), timeout=60)
    if response.text:
        username, password = response.text.split(":", 1)
        tidal = tidal_dl.TidalDL()
        try:
            tidal.login_by_credentials(username, password)  # Custom method; adapt as needed
            TIDAL_SETTINGS.read()
            TIDAL_TOKEN.read("./tidal-dl.token.json")
            set_db.set_variable("TIDAL_AUTH", True, False, None)
            await response.reply("Tidal authenticated successfully!")
        except Exception as e:
            await response.reply(f"Tidal authentication failed: {e}")
    else:
        await message.reply("No valid response received. Authentication cancelled.")

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
