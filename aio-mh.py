import telegram
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
import sqlite3
from datetime import datetime, timedelta
import subprocess
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

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
    await update.message.reply_text("Please send payment proof to subscribe.")

# Handle Payment Proof
async def handle_payment(update, context):
    user_id = update.message.from_user.id
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (user_id, payment_status) VALUES (?, 'pending')", (user_id,))
    conn.commit()
    conn.close()
    
    # Reply to user
    await update.message.reply_text("Payment proof received. Waiting for admin approval.")
    
    # Send notification to admin
    admin_id = ADMIN_ID
    photo = update.message.photo[-1]  # Get the highest resolution photo
    await context.bot.send_photo(
        chat_id=admin_id,
        photo=photo.file_id,
        caption=f"New payment proof from user ID: {user_id}\nUse /approve {user_id} to approve."
    )

# Admin Approve Command
async def approve(update, context):
    if update.message.from_user.id != ADMIN_ID:
        return
    try:
        user_id = int(context.args[0])
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute("UPDATE users SET approved=1, subscription_start=?, subscription_end=? WHERE user_id=?",
                  (datetime.now().strftime('%Y-%m-%d'), (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d'), user_id))
        conn.commit()
        
        # Fetch subscription end date for notification
        c.execute("SELECT subscription_end FROM users WHERE user_id=?", (user_id,))
        subscription_end = c.fetchone()[0]
        conn.close()
        
        # Notify admin
        await update.message.reply_text(f"User {user_id} approved!")
        
        # Notify user
        await context.bot.send_message(
            chat_id=user_id,
            text=f"Your subscription has been approved!\nValid until: {subscription_end}"
        )
    except:
        await update.message.reply_text("Usage: /approve <user_id>")

# Download Command
async def download(update, context):
    user_id = update.message.from_user.id
    if not check_subscription(user_id):
        await update.message.reply_text("Your subscription has expired. Please renew.")
        return
    try:
        song_url = context.args[0]
        # Use dynamic path for the MH script (updated to aio-mh.py)
        script_path = os.path.join(os.path.dirname(__file__), 'aio-mh.py')  # Replace with actual MH script name
        result = subprocess.run(['python', script_path, song_url], capture_output=True, text=True)
        await update.message.reply_text(f"Download complete: {result.stdout}")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}\nUsage: /download <song_url>")

# Main Function
def main():
    init_db()
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("download", download))
    application.add_handler(MessageHandler(filters.PHOTO, handle_payment))
    
    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()