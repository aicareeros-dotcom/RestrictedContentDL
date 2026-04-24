# Copyright (C) @TheSmartBisnu
# Upgraded Version by ChatGPT

import os
import asyncio
from threading import Thread
from flask import Flask

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from config import PyroConf
from logger import LOGGER

# =======================
# FLASK SERVER (RENDER FIX)
# =======================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is LIVE 🚀"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)

# =======================
# BOT CLIENT
# =======================
app = Client(
    "media_bot",
    api_id=PyroConf.API_ID,
    api_hash=PyroConf.API_HASH,
    bot_token=PyroConf.BOT_TOKEN,
    workers=100,
    parse_mode=ParseMode.MARKDOWN
)

user = Client(
    "user_session",
    api_id=PyroConf.API_ID,
    api_hash=PyroConf.API_HASH,
    session_string=PyroConf.SESSION_STRING
)

# =======================
# GLOBAL STATE
# =======================
RUNNING_TASKS = set()
download_semaphore = None
forward_chat_id = None

# =======================
# TASK TRACKER (SAFE)
# =======================
def track_task(coro):
    task = asyncio.create_task(coro)
    RUNNING_TASKS.add(task)

    def done_callback(t):
        RUNNING_TASKS.discard(task)

    task.add_done_callback(done_callback)
    return task

# =======================
# START COMMAND
# =======================
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply(
        "👋 **Welcome to Media Bot Pro 🚀**\n\n"
        "📥 Send Telegram post link to download\n"
        "🧹 /cleanup - clean storage\n"
        "⚡ Fast + Stable + Render Ready"
    )

# =======================
# HELP COMMAND
# =======================
@app.on_message(filters.command("help") & filters.private)
async def help_cmd(_, message: Message):
    await message.reply(
        "💡 **Help Menu**\n\n"
        "➤ Send link → download media\n"
        "➤ /cleanup → clear storage\n"
    )

# =======================
# CLEANUP COMMAND
# =======================
@app.on_message(filters.command("cleanup") & filters.private)
async def cleanup(_, message: Message):
    try:
        from helpers.files import cleanup_downloads_root, get_readable_file_size

        files_removed, bytes_freed = cleanup_downloads_root()
        await message.reply(
            f"🧹 Cleaned `{files_removed}` files\n"
            f"💾 Freed `{get_readable_file_size(bytes_freed)}`"
        )
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# =======================
# MAIN DOWNLOAD HANDLER
# =======================
@app.on_message(filters.private & filters.text)
async def handle_message(client, message: Message):
    text = message.text.strip()

    if "http" not in text:
        return

    await message.reply("⏳ Processing your request...")

    try:
        from helpers.forward import resolve_forward_chat_id
        from helpers.msg import get_raw_text
        from helpers.utils import send_media

        # process task safely
        async def process():
            try:
                await send_media(app, user, message, text)
            except Exception as e:
                await message.reply(f"❌ Failed: {e}")

        track_task(process())

    except Exception as e:
        await message.reply(f"❌ Error: {e}")

# =======================
# INIT
# =======================
async def initialize():
    global download_semaphore, forward_chat_id

    download_semaphore = asyncio.Semaphore(PyroConf.MAX_CONCURRENT_DOWNLOADS)

    if PyroConf.FORWARD_CHAT_ID:
        try:
            from helpers.forward import resolve_forward_chat_id
            forward_chat_id = await resolve_forward_chat_id(PyroConf.FORWARD_CHAT_ID)
        except Exception as e:
            LOGGER(__name__).error(f"Forward error: {e}")

# =======================
# START SERVICES (FIXED)
# =======================
async def start_services():
    Thread(target=run_web, daemon=True).start()

    await initialize()

    try:
        await user.start()
        LOGGER(__name__).info("User session started")
    except Exception as e:
        LOGGER(__name__).error(f"User session failed: {e}")

    await app.start()
    print("🚀 Bot Running Successfully")

    await asyncio.Event().wait()

# =======================
# MAIN ENTRY
# =======================
if __name__ == "__main__":
    try:
        asyncio.run(start_services())
    except Exception as e:
        LOGGER(__name__).error(f"Fatal Error: {e}")
