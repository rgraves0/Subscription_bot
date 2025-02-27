# bot/__init__.py
import logging
from .config import Config

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("aiohttp").setLevel(logging.WARNING)
logging.getLogger("charset_normalizer").setLevel(logging.WARNING)
logging.getLogger("Librespot:Session").setLevel(logging.WARNING)
logging.getLogger("Librespot:MercuryClient").setLevel(logging.WARNING)
logging.getLogger("Librespot:TokenProvider").setLevel(logging.WARNING)
logging.getLogger("librespot.audio").setLevel(logging.WARNING)
logging.getLogger("Librespot:ApiClient").setLevel(logging.WARNING)
logging.getLogger("pydub").setLevel(logging.WARNING)

bot = Config.BOT_USERNAME

class CMD(object):
    START = ["start", f"start@{bot}"]
    HELP = ["help", f"help@{bot}"]
    SETTINGS = ["settings", f"settings@{bot}"]
    DOWNLOAD = ["dl", f"dl@{bot}"]
    AUTH = ["auth", f"auth@{bot}"]
    ADD_ADMIN = ["sudo", f"sudo@{bot}"]
    SHELL = ["shell", f"shell@{bot}"]

def download_song(song_url):
    # Placeholder for actual download logic
    LOGGER.info(f"Downloading song: {song_url}")
    return "Download completed (simulated)"