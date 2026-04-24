# ===== RENDER LIVE & 24/7 CONFIG =====
import os
import threading
import asyncio
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Status: 100% Online 🚀", 200

def run_flask():
    # Render hamesha port 10000 mangta hai
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# Flask ko background thread mein chalana zaroori hai
threading.Thread(target=run_flask, daemon=True).start()

# =====================================

import shutil
import psutil
from time import time

from pyleaves import Leaves
from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid, BadRequest, FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Helpers aur Config (Aapki purani files se)
from helpers.utils import processMediaGroup, progressArgs, send_media
from helpers.forward import check_forward_permission, resolve_forward_chat_id
from helpers.files import (
    get_download_path, fileSizeLimit, get_readable_file_size, 
    get_readable_time, cleanup_download, cleanup_downloads_root
)
from helpers.msg import getChatMsgID, get_file_name, get_raw_text
from config import PyroConf
from logger import LOGGER

# --- Clients Setup ---
bot = Client(
    "media_bot",
    api_id=PyroConf.API_ID,
    api_hash=PyroConf.API_HASH,
    bot_token=PyroConf.BOT_TOKEN,
    workers=100,
    parse_mode=ParseMode.MARKDOWN,
    max_concurrent_transmissions=1,
    sleep_threshold=30,
)

user = Client(
    "user_session",
    api_id=PyroConf.API_ID,
    api_hash=PyroConf.API_HASH,
    session_string=PyroConf.SESSION_STRING,
    workers=100,
    max_concurrent_transmissions=1,
    sleep_threshold=30,
)

RUNNING_TASKS = set()
download_semaphore = None
forward_chat_id = None

# --- Handlers ---

@bot.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    welcome_text = (
        "👋 **Welcome to Media Downloader Bot!**\n\n"
        "I am running 24/7 on Render! 🚀\n"
        "Send me a Telegram link to start."
    )
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Update Channel", url="https://t.me/itsSmartDev")]]
    )
    await message.reply(welcome_text, reply_markup=markup, disable_web_page_preview=True)

@bot.on_message(filters.command("help") & filters.private)
async def help_command(_, message: Message):
    help_text = (
        "💡 **Media Downloader Bot Help**\n\n"
        "➤ Send a link to download media.\n"
        "➤ Use /cleanup to clear space.\n"
        "➤ Use /stats to check server health."
    )
    await message.reply(help_text)

@bot.on_message(filters.command("cleanup") & filters.private)
async def cleanup_storage(_, message: Message):
    try:
        files_removed, bytes_freed = cleanup_downloads_root()
        await message.reply(f"🧹 Freed `{get_readable_file_size(bytes_freed)}` from server.")
    except Exception as e:
        await message.reply("❌ Cleanup failed.")

# --- Initialization & Main Loop ---

async def initialize():
    global download_semaphore, forward_chat_id
    download_semaphore = asyncio.Semaphore(PyroConf.MAX_CONCURRENT_DOWNLOADS)
    if PyroConf.FORWARD_CHAT_ID:
        try:
            forward_chat_id = await resolve_forward_chat_id(PyroConf.FORWARD_CHAT_ID)
            LOGGER(__name__).info(f"Forward ID set to: {forward_chat_id}")
        except:
            LOGGER(__name__).error("Failed to resolve Forward Chat ID")

async def main():
    LOGGER(__name__).info("Bot is starting...")
    await initialize()
    
    # Start User Session
    try:
        await user.start()
        LOGGER(__name__).info("✅ User session is live!")
    except Exception as e:
        LOGGER(__name__).error(f"❌ User session error: {e}")

    # Start Bot
    try:
        await bot.start()
        LOGGER(__name__).info("✅ Bot is online and ready!")
    except Exception as e:
        LOGGER(__name__).error(f"❌ Bot start error: {e}")
        return

    # Keep the bot running forever
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        LOGGER(__name__).info("Stopping...")
    except Exception as err:
        LOGGER(__name__).error(f"Fatal Error: {err}")
        
