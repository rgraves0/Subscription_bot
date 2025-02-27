import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import sqlite3
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import subprocess
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

# Check if environment variables are set
if not BOT_TOKEN or not ADMIN_ID:
    raise ValueError("BOT_TOKEN and ADMIN_ID must be set in environment variables or .env file")
try:
    ADMIN_ID = int(ADMIN_ID)
except ValueError:
    raise ValueError("ADMIN_ID must be a valid integer")

# Database Setup
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, subscription_start DATE, subscription_end DATE, 
                 payment_status TEXT DEFAULT 'pending', approved BOOLEAN DEFAULT FALSE)''')
    conn.commit()
    conn.close()

# Check Subscription
def check_subscription(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("SELECT subscription_end FROM users WHERE user_id=? AND approved=1", (user_id,))
    result = c.fetchone()
    conn.close()
    if result and datetime.strptime(result[0], '%Y-%m-%d') > datetime.now():
        return True
    return False

# Start Command
async def start(update, context):
    user_id = update.message.from_user.id
    await update.message.reply_text("Welcome! To subscribe, please send a payment proof photo.")

# Handle Payment Proof
async def handle_payment(update, context):
    user_id = update.message.from_user.id
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, payment_status) VALUES (?, 'pending')", (user_id,))
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"Your payment proof has been received! User ID: {user_id}\n"
        "Status: Waiting for admin approval.\n"
        "Please wait up to 24 hours for the admin to review your request."
    )
    
    admin_id = ADMIN_ID
    try:
        photo = update.message.photo[-1]
        await context.bot.send_photo(
            chat_id=admin_id,
            photo=photo.file_id,
            caption=f"New payment proof received!\nUser ID: {user_id}\nUse /approve {user_id} to approve."
        )
        logger.info(f"Payment proof successfully sent to admin {admin_id} for user {user_id}")
    except telegram.error.BadRequest as e:
        logger.error(f"Failed to send payment proof to admin {admin_id}: {e}")
        await update.message.reply_text(
            "Failed to notify the admin. Please ask the admin to start the bot with /start and try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error while sending payment proof to admin {admin_id}: {e}")
        await update.message.reply_text(
            "An unexpected error occurred while notifying the admin. Please try again later."
        )

# Admin Approve Command
async def approve(update, context):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        start_date = datetime.now().strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        c.execute("UPDATE users SET approved=1, subscription_start=?, subscription_end=? WHERE user_id=?",
                  (start_date, end_date, user_id))
        conn.commit()
        
        c.execute("SELECT subscription_start, subscription_end FROM users WHERE user_id=?", (user_id,))
        subscription_dates = c.fetchone()
        conn.close()
        
        await update.message.reply_text(f"User {user_id} approved!\nSubscription valid from {subscription_dates[0]} to {subscription_dates[1]}")
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Your subscription has been approved!\n"
                 f"Start Date: {subscription_dates[0]}\n"
                 f"End Date: {subscription_dates[1]}"
        )
    except:
        await update.message.reply_text("Usage: /approve <user_id>")

# Download Command
async def download(update, context):
    user_id = update.message.from_user.id
    if not check_subscription(user_id):
        await update.message.reply_text("Your subscription has expired. Please renew by sending a new payment proof.")
        return
    try:
        song_url = context.args[0]
        script_path = os.path.join(os.path.dirname(__file__), 'bot', '__main__.py')
        result = subprocess.run(['python', script_path, song_url], capture_output=True, text=True)
        if result.stderr:
            logger.error(f"Download error for {song_url}: {result.stderr}")
            await update.message.reply_text(f"Download failed: {result.stderr}")
        else:
            await update.message.reply_text(f"Download complete: {result.stdout}")
    except FileNotFoundError:
        logger.error("bot/__main__.py not found in the directory")
        await update.message.reply_text("Download functionality is disabled. Missing bot/__main__.py script.")
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        await update.message.reply_text(f"Error: {str(e)}\nUsage: /download <song_url>")

# Main Function
def main():
    init_db()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(MessageHandler(filters.PHOTO, handle_payment))
    
    application.run_polling()

if __name__ == '__main__':
    main()