# Copyright (C) @TheSmartBisnu
# Channel: https://t.me/itsSmartDev

import os
import shutil
import psutil
import asyncio
from threading import Thread
from flask import Flask
from time import time

from pyrogram.enums import ParseMode
from pyrogram import Client, filters
from pyrogram.errors import PeerIdInvalid, BadRequest, FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# Aapke existing helper imports (Same to Same)
from helpers.utils import (
    processMediaGroup,
    progressArgs,
    send_media
)
from helpers.forward import check_forward_permission, resolve_forward_chat_id
from helpers.files import (
    get_download_path,
    fileSizeLimit,
    get_readable_file_size,
    get_readable_time,
    cleanup_download,
    cleanup_downloads_root
)
from helpers.msg import (
    getChatMsgID,
    get_file_name,
    get_raw_text
)
from config import PyroConf
from logger import LOGGER

# ===== RENDER WEB SERVER (run_web function) =====
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is LIVE 🚀"

def run_web():
    # Render hamesha environment se port leta hai
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# ===== BOT CLIENTS (Client name 'app' for your logic) =====
app = Client(
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

def track_task(coro):
    task = asyncio.create_task(coro)
    RUNNING_TASKS.add(task)
    def _remove(_):
        RUNNING_TASKS.discard(task)
    task.add_done_callback(_remove)
    return task

# --- Original Handlers (Same to Same) ---

@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    welcome_text = (
        "👋 **Welcome to Media Downloader Bot!**\n\n"
        "I can grab photos, videos, audio, and documents from any Telegram post.\n"
        "Ready? Send me a Telegram post link!"
    )
    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("Update Channel", url="https://t.me/itsSmartDev")]]
    )
    await message.reply(welcome_text, reply_markup=markup, disable_web_page_preview=True)

@app.on_message(filters.command("help") & filters.private)
async def help_command(_, message: Message):
    help_text = (
        "💡 **Media Downloader Bot Help**\n\n"
        "➤ **Download Media**\n"
        "   – Send `/dl <post_URL>` **or** just paste a link.\n\n"
        "➤ **Cleanup** → `/cleanup`\n"
    )
    await message.reply(help_text)

@app.on_message(filters.command("cleanup") & filters.private)
async def cleanup_storage(_, message: Message):
    try:
        files_removed, bytes_freed = cleanup_downloads_root()
        await message.reply(f"🧹 Removed `{files_removed}` files, freed `{get_readable_file_size(bytes_freed)}`.")
    except Exception as e:
        await message.reply("❌ Cleanup failed.")

async def initialize():
    global download_semaphore, forward_chat_id
    download_semaphore = asyncio.Semaphore(PyroConf.MAX_CONCURRENT_DOWNLOADS)
    if PyroConf.FORWARD_CHAT_ID:
        try:
            forward_chat_id = await resolve_forward_chat_id(PyroConf.FORWARD_CHAT_ID)
        except Exception as e:
            LOGGER(__name__).error(f"Forward resolution error: {e}")

# ===== AAPKA MANGAA HUA FINAL LOGIC =====

async def start_services():
    # Flask server ko background thread mein start karein
    Thread(target=run_web, daemon=True).start()
    
    # Init aur User session start
    await initialize()
    try:
        await user.start()
        LOGGER(__name__).info("User Session Started!")
    except Exception as e:
        LOGGER(__name__).error(f"User Session Error: {e}")

    # Main Bot (app) ko start karein
    await app.start()
    print("Bot Running...")
    
    # Bot ko zinda rakhne ke liye event wait
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        pass
    except Exception as err:
        LOGGER(__name__).error(f"Fatal Crash: {err}")
    finally:
        LOGGER(__name__).info("Bot Stopped")
        
