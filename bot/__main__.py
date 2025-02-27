import os
import sys
import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from bot import Config, LOGGER, CMD  # CMD ကို bot/__init__.py ထဲမှာ define လုပ်ထားရမယ်
from bot.helpers.tidal_func.settings import TIDAL_SETTINGS, TIDAL_TOKEN
from bot.helpers.database.postgres_impl import set_db
from bot.helpers.translations import lang  # Translation strings
from bot.helpers.tidal_func.apikey import getItem as tidalAPI_getItem  # Tidal API key helper
from bot.helpers.tidal_func.events import loginTidal, getapiInfoTidal, checkAPITidal
from bot.helpers.buttons.settings_buttons import *  # Settings buttons
import tidal_dl

plugins = dict(root="bot/modules")

async def tidal_authenticate(username, password):
    try:
        tidal = tidal_dl.TidalDL()
        tidal.login_by_credentials(username, password)  # Custom method လိုအပ်နိုင်
        TIDAL_SETTINGS.read()
        TIDAL_TOKEN.read("./tidal-dl.token.json")
        set_db.set_variable("TIDAL_AUTH", True, False, None)
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
    tidal_quality, _ = set_db.get_variable("TIDAL_QUALITY")
    if "tidal" in url.lower():
        if tidal_auth and tidal_auth[0]:
            tidal = tidal_dl.TidalDL()
            tidal.settings.quality = tidal_quality if tidal_quality else "LOSSLESS"  # Use DB quality
            tidal.download(url)
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
        if message.from_user.id == Config.ADMIN_ID:
            await func(client, message)
        else:
            await message.reply("This command is for admins only!")
    return wrapper

# Tidal Auth Command
@Bot.on_message(filters.command("tidal_auth") & filters.private)
@admin_only
async def tidal_auth_command(client: Bot, message: Message):
    await message.reply("Please send your Tidal username and password in the format:\n`username:password`")
    response = await client.listen.Message(filters.user(message.from_user.id), timeout=60)
    if response.text:
        username, password = response.text.split(":", 1)
        if await tidal_authenticate(username, password):
            await response.reply("Tidal authenticated successfully!")
        else:
            await response.reply("Tidal authentication failed.")
    else:
        await message.reply("No valid response received. Authentication cancelled.")

# Settings Command from settings.py
@Bot.on_message(filters.command(CMD.SETTINGS))
@admin_only
async def settings(bot, update: Message):
    await bot.send_message(
        chat_id=update.chat.id,
        text=lang.select.INIT_SETTINGS_MENU,
        reply_markup=main_menu_set()
    )

# Tidal Settings Panel from settings.py
@Bot.on_callback_query(filters.regex(pattern=r"^tidalPanel"))
@admin_only
async def tidal_panel_cb(bot, update):
    quality, _ = set_db.get_variable("TIDAL_QUALITY")
    api_index = TIDAL_SETTINGS.apiKeyIndex
    db_auth, _ = set_db.get_variable("TIDAL_AUTH")
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.select.TIDAL_SETTINGS_PANEL.format(
            quality if quality else "LOSSLESS",
            api_index,
            db_auth
        ),
        reply_markup=tidal_menu_set()
    )

# API Settings for Tidal from settings.py
@Bot.on_callback_query(filters.regex(pattern=r"^apiTidal"))
@admin_only
async def tidal_api_cb(bot, update, refresh=False):
    option = update.data.split("_")[1]
    current_api = TIDAL_SETTINGS.apiKeyIndex
    api, platform, validity, quality = await getapiInfoTidal()
    info = ""
    for number in api:
        info += f"<b>● {number} - {platform[number]}</b>\nFormats - <code>{quality[number]}</code>\nValid - <code>{validity[number]}</code>\n"
    if option == "panel" or refresh:
        await bot.edit_message_text(
            chat_id=update.message.chat.id,
            message_id=update.message.id,
            text=lang.select.TIDAL_SELECT_API_KEY.format(
                tidalAPI_getItem(current_api)['platform'],
                tidalAPI_getItem(current_api)['formats'],
                tidalAPI_getItem(current_api)['valid'],
                info
            ),
            reply_markup=tidal_api_set(api, platform)
        )
    else:
        set_db.set_variable("TIDAL_API_KEY_INDEX", option, False, None)
        await update.answer(
            lang.select.TIDAL_API_KEY_CHANGED.format(
                int(option),
                tidalAPI_getItem(int(option))['platform'],
            )
        )
        TIDAL_SETTINGS.read()
        await checkAPITidal()
        try:
            await tidal_api_cb(bot, update, True)
        except:
            pass

# Quality Options for Tidal from settings.py
@Bot.on_callback_query(filters.regex(pattern=r"^QA_tidal"))
@admin_only
async def quality_cb(bot, update):
    current_quality, _ = set_db.get_variable("TIDAL_QUALITY")
    if not current_quality:
        current_quality = "Default"
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.select.QUALITY_SET_PANEL.format("Tidal", current_quality),
        reply_markup=quality_buttons("tidal", None)
    )

# Set Quality for Tidal from settings.py
@Bot.on_callback_query(filters.regex(pattern=r"^SQA_tidal"))
@admin_only
async def set_quality_cb(bot, update):
    quality = update.data.split("_")[2]
    set_db.set_variable("TIDAL_QUALITY", quality, False, None)
    current_quality, _ = set_db.get_variable("TIDAL_QUALITY")
    if not current_quality:
        current_quality = "Default"
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.select.QUALITY_SET_PANEL.format("Tidal", current_quality),
        reply_markup=quality_buttons("tidal", None)
    )

# Main Menu Callback from settings.py
@Bot.on_callback_query(filters.regex(pattern=r"^main_menu"))
@admin_only
async def main_menu_cb(bot, update):
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.select.INIT_SETTINGS_MENU,
        reply_markup=main_menu_set()
    )

# Close Callback from settings.py
@Bot.on_callback_query(filters.regex(pattern=r"^close"))
@admin_only
async def close_cb(bot, update):
    await bot.delete_messages(
        chat_id=update.message.chat.id,
        message_ids=update.message.id
    )

async def main():
    if not os.path.isdir(Config.DOWNLOAD_BASE_DIR):
        os.makedirs(Config.DOWNLOAD_BASE_DIR)

    app = Bot()

    if len(sys.argv) > 1:
        url = sys.argv[1]
        await app.start()
        try:
            result = await download_url(url)
            print(result)
        finally:
            await app.stop()
    else:
        await app.start()
        try:
            await app.idle()
        finally:
            await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
