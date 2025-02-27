import os
import sys
import asyncio
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import Message
from pyrogram.errors import MessageNotModified

from bot import Config, LOGGER, CMD  # LOGGER က bot.logger ကနေ လာတာပါ
from bot.helpers.translations import lang
from bot.helpers.utils.clean import clean_up
from bot.helpers.utils.check_link import check_link
from bot.helpers.database.postgres_impl import set_db, user_settings, users_db, admins_db, chats_db
from bot.helpers.utils.auth_check import check_id, get_chats, checkLogins
from bot.helpers.tidal_func.apikey import getItem as tidalAPI_getItem
from bot.helpers.tidal_func.settings import TIDAL_SETTINGS, TIDAL_TOKEN
from bot.helpers.tidal_func.events import loginTidal, getapiInfoTidal, checkAPITidal, startTidal
from bot.helpers.tidal_func.tidal import TIDAL_API
from bot.helpers.tidal_func.enums import AudioQuality
from bot.helpers.qobuz.handler import qobuz
from bot.helpers.qobuz.qopy import qobuz_api
from bot.helpers.qobuz.utils import human_quality
from bot.helpers.deezer.handler import deezerdl
from bot.helpers.kkbox.kkbox_helper import kkbox
from bot.helpers.kkbox.kkapi import kkbox_api
from bot.helpers.spotify.handler import spotify_dl
from bot.helpers.buttons.settings_buttons import *

plugins = dict(root="bot/modules")

# Load Configurations
async def loadConfigs():
    # Tidal
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
            LOGGER.warning("Deezer BF Secret not provided.")
            sys.exit(1)
        if Config.DEEZER_TRACK_URL_KEY == "":
            LOGGER.warning("Deezer Track URL Key not provided.")
            sys.exit(1)
        await deezerdl.login()
    elif Config.DEEZER_ARL != "":
        await deezerdl.login(True)
    else:
        set_db.set_variable("DEEZER_AUTH", False, False, None)
    # SPOTIFY
    if not "" in {Config.SPOTIFY_EMAIL, Config.SPOTIFY_PASS}:
        await spotify_dl.login()
        set_db.set_variable("SPOTIFY_AUTH", True, False, None)
    else:
        set_db.set_variable("SPOTIFY_AUTH", False, False, None)

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
        await get_chats()  # Load authorized users/chats/admins
        LOGGER.info("❤ MUSIC HELPER BOT BETA v0.30 STARTED SUCCESSFULLY ❤")

    async def stop(self, *args):
        await super().stop()
        LOGGER.info('Bot Exited Successfully ! Bye..........')

# Filters
def admin_only(func):
    async def wrapper(client, message: Message):
        if message.from_user.id == Config.ADMIN_ID or admins_db.check_admin(message.from_user.id):
            await func(client, message)
        else:
            await message.reply("This command is for admins only!")
    return wrapper

def auth_only(func):
    async def wrapper(client, message: Message):
        if await check_id(message=message):
            await func(client, message)
        else:
            await message.reply("You are not authorized to use this bot. Contact an admin to get approved.")
    return wrapper

# Handlers from basic.py
@Bot.on_message(filters.command(CMD.START))
async def start(bot, update: Message):
    await bot.send_message(
        chat_id=update.chat.id,
        text=lang.select.WELCOME_MSG.format(update.from_user.first_name),
        reply_to_message_id=update.id
    )

@Bot.on_message(filters.command(CMD.AUTH))
@admin_only
async def auth_chat(bot, update: Message):
    if update.reply_to_message:
        chat_id = update.reply_to_message.from_user.id
    else:
        try:
            chat_id = int(update.text.split()[1])
        except:
            chat_id = update.chat.id
    
    if str(chat_id).startswith("-100"):
        type = "chat"
        chats_db.set_chats(int(chat_id))
    else:
        type = "user"
        users_db.set_users(int(chat_id))
    await get_chats()
    await bot.send_message(
        chat_id=update.chat.id,
        text=lang.select.CHAT_AUTH_SUCCESS.format(type, chat_id),
        reply_to_message_id=update.id
    )

@Bot.on_message(filters.command(CMD.ADD_ADMIN))
@admin_only
async def add_admin(bot, update: Message):
    if update.reply_to_message:
        admin_id = update.reply_to_message.from_user.id
    else:
        try:
            admin_id = update.text.split()[1]
            if admin_id.isnumeric():
                admin_id = int(admin_id)
            else:
                admin_id = None
        except:
            admin_id = None
    if admin_id:
        admins_db.set_admins(int(admin_id))
        await get_chats()
        await bot.send_message(
            chat_id=update.chat.id,
            text=lang.select.ADD_ADMIN_SUCCESS.format(admin_id),
            reply_to_message_id=update.id
        )
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text=lang.select.NO_ID_TO_AUTH,
            reply_to_message_id=update.id
        )

# Handlers from settings.py
@Bot.on_message(filters.command(CMD.SETTINGS))
@auth_only
async def settings(bot, update: Message):
    await bot.send_message(
        chat_id=update.chat.id,
        text=lang.select.INIT_SETTINGS_MENU,
        reply_markup=main_menu_set()
    )

@Bot.on_callback_query(filters.regex(pattern=r"^tidalPanel"))
@auth_only
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

@Bot.on_callback_query(filters.regex(pattern=r"^kkboxPanel"))
@auth_only
async def kkbox_panel_cb(bot, update):
    quality, _ = set_db.get_variable("KKBOX_QUALITY")
    auth, _ = set_db.get_variable("KKBOX_AUTH")
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.select.KKBOX_SETTINGS_PANEL.format(
            quality.upper() if quality else "N/A",
            auth
        ),
        reply_markup=kkbox_menu_set()
    )

@Bot.on_callback_query(filters.regex(pattern=r"^qobuzPanel"))
@auth_only
async def qobuz_panel_cb(bot, update):
    quality, _ = set_db.get_variable("QOBUZ_QUALITY")
    quality = await human_quality(int(quality)) if quality else "N/A"
    auth, _ = set_db.get_variable("QOBUZ_AUTH")
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.select.QOBUZ_SETTINGS_PANEL.format(
            quality,
            auth
        ),
        reply_markup=qobuz_menu_set()
    )

@Bot.on_callback_query(filters.regex(pattern=r"^deezerPanel"))
@auth_only
async def deezer_panel_cb(bot, update):
    quality, _ = set_db.get_variable("DEEZER_QUALITY")
    spatial, _ = set_db.get_variable("DEEZER_SPATIAL")
    quality = await deezerdl.parse_quality(quality, False, True) if quality else "N/A"
    auth, _ = set_db.get_variable("DEEZER_AUTH")
    auth_by = 'By ARL' if Config.DEEZER_ARL != "" else 'By Creds'
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.select.DEEZER_SETTINGS_PANEL.format(
            quality,
            auth,
            auth_by,
            spatial
        ),
        reply_markup=deezer_menu_set()
    )

@Bot.on_callback_query(filters.regex(pattern=r"^apiTidal"))
@auth_only
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

@Bot.on_callback_query(filters.regex(pattern=r"^QA_tidal"))
@auth_only
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

@Bot.on_callback_query(filters.regex(pattern=r"^SQA_tidal"))
@auth_only
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

@Bot.on_callback_query(filters.regex(pattern=r"^main_menu"))
@auth_only
async def main_menu_cb(bot, update):
    await bot.edit_message_text(
        chat_id=update.message.chat.id,
        message_id=update.message.id,
        text=lang.select.INIT_SETTINGS_MENU,
        reply_markup=main_menu_set()
    )

@Bot.on_callback_query(filters.regex(pattern=r"^close"))
@auth_only
async def close_cb(bot, update):
    await bot.delete_messages(
        chat_id=update.message.chat.id,
        message_ids=update.message.id
    )

# Handlers from download.py
@Bot.on_message(filters.command(CMD.DOWNLOAD))
@auth_only
async def download_track(bot, update: Message):
    try:
        if update.reply_to_message:
            link = update.reply_to_message.text
            reply_to_id = update.reply_to_message.id
        else:
            link = update.text.split(" ", maxsplit=1)[1]
            reply_to_id = update.id
    except:
        return await bot.send_message(
            chat_id=update.chat.id,
            text=lang.select.ERR_NO_LINK,
            reply_to_message_id=update.id
        )
    
    if link:
        provider = await check_link(link)
        if provider:
            err, err_msg = await checkLogins(provider)
            if err:
                return await bot.send_message(
                    chat_id=update.chat.id,
                    text=err_msg,
                    reply_to_message_id=update.id
                )
        else:
            return await bot.send_message(
                chat_id=update.chat.id,
                text=lang.select.ERR_LINK_RECOGNITION,
                reply_to_message_id=update.id
            )
        
        LOGGER.info(f"Download Initiated By - {update.from_user.first_name}")
        msg = await bot.send_message(
            chat_id=update.chat.id,
            text=lang.select.START_DOWNLOAD,
            reply_to_message_id=update.id
        )
        u_name = f'<a href="tg://user?id={update.from_user.id}">{update.from_user.first_name}</a>'

        user_settings.set_var(update.chat.id, "ON_TASK", True)
        try:
            if provider == "tidal":
                await startTidal(link, bot, update.chat.id, reply_to_id, update.from_user.id, u_name)
            elif provider == "kkbox":
                await kkbox.start(link, bot, update, reply_to_id, u_name)
            elif provider == 'qobuz':
                await qobuz.start(link, bot, update, reply_to_id, u_name)
            elif provider == 'deezer':
                await deezerdl.start(link, bot, update, reply_to_id, u_name)
            elif provider == 'spotify':
                await spotify_dl.start(link, bot, update, reply_to_id, u_name)
            await bot.delete_messages(update.chat.id, msg.id)
            await bot.send_message(
                chat_id=update.chat.id,
                text=lang.select.TASK_COMPLETED,
                reply_to_message_id=update.id
            )
        except Exception as e:
            LOGGER.warning(e)
            await bot.send_message(
                chat_id=update.chat.id,
                text=str(e),
                reply_to_message_id=update.id
            )
        user_settings.set_var(update.chat.id, "ON_TASK", False)
        await clean_up(reply_to_id, provider)

# Tidal Auth Command
@Bot.on_message(filters.command("tidal_auth") & filters.private)
@admin_only
async def tidal_auth_command(client: Bot, message: Message):
    msg = await message.reply("Initiating Tidal authentication...")
    success, error = await loginTidal(client, msg, message.chat.id)
    if not success:
        await msg.edit(f"Tidal authentication failed: {error}")

async def main():
    if not os.path.isdir(Config.DOWNLOAD_BASE_DIR):
        os.makedirs(Config.DOWNLOAD_BASE_DIR)

    app = Bot()

    if len(sys.argv) > 1:  # Command-line mode
        url = sys.argv[1]
        await app.start()
        try:
            provider = await check_link(url)
            if provider == "tidal":
                quality, _ = set_db.get_variable("TIDAL_QUALITY")
                TIDAL_API.apiKey = tidalAPI_getItem(TIDAL_SETTINGS.apiKeyIndex)
                etype, obj = TIDAL_API.getByString(url)
                if etype == Type.Track:
                    track = obj
                    album = TIDAL_API.getAlbum(track.album.id)
                    stream = TIDAL_API.getStreamUrl(track.id, TIDAL_SETTINGS.getAudioQuality(quality) if quality else AudioQuality.LOSSLESS)
                    path = f"{Config.DOWNLOAD_BASE_DIR}/tidal/{track.id}_{track.title}{stream.ext}"
                    await downloadTrack(track, album, path=path)
                    print("Tidal download completed")
                else:
                    print("Only Tidal tracks are supported in command-line mode for now.")
            else:
                print("Only Tidal is supported in command-line mode for now.")
        finally:
            await app.stop()
    else:  # Telegram bot mode
        await app.start()
        try:
            await app.idle()
        finally:
            await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
