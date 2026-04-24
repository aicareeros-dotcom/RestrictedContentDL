# Copyright (C) @TheSmartBisnu
# Final Render-Ready Version 🚀

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
# FLASK SERVER (RENDER LIVE FIX)
# =======================
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    # Render isi response ka wait karta hai 'Live' dikhane ke liye
    return "Bot is Status: 100% Online 🚀", 200

def run_web():
    # Port 10000 hardcoded for Render
    flask_app.run(host="0.0.0.0", port=10000, debug=False, use_reloader=False)

# =======================
# BOT CLIENTS
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
# GLOBAL STATE & TRACKER
# =======================
RUNNING_TASKS = set()
download_semaphore = None
forward_chat_id = None

def track_task(coro):
    task = asyncio.create_task(coro)
    RUNNING_TASKS.add(task)
    def done_callback(t):
        RUNNING_TASKS.discard(task)
    task.add_done_callback(done_callback)
    return task

# =======================
# HANDLERS (Same to Same)
# =======================
@app.on_message(filters.command("start") & filters.private)
async def start(_, message: Message):
    await message.reply(
        "👋 **Bot is Active!**\n\n"
        "Render par status thodi der mein **Live** ho jayega.\n"
        "Ab aap link bhej sakte hain."
    )

@app.on_message(filters.command("cleanup") & filters.private)
async def cleanup(_, message: Message):
    try:
        from helpers.files import cleanup_downloads_root, get_readable_file_size
        files_removed, bytes_freed = cleanup_downloads_root()
        await message.reply(f"🧹 Freed `{get_readable_file_size(bytes_freed)}` space.")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")

@app.on_message(filters.private & filters.text)
async def handle_message(client, message: Message):
    text = message.text.strip()
    if "http" not in text:
        return
    
    try:
        from helpers.utils import send_media
        async def process():
            try:
                await send_media(app, user, message, text)
            except Exception as e:
                await message.reply(f"❌ Error: {e}")
        track_task(process())
    except Exception as e:
        await message.reply(f"❌ Crash: {e}")

# =======================
# START SERVICES (FIXED)
# =======================
async def initialize():
    global download_semaphore, forward_chat_id
    download_semaphore = asyncio.Semaphore(PyroConf.MAX_CONCURRENT_DOWNLOADS)
    if PyroConf.FORWARD_CHAT_ID:
        try:
            from helpers.forward import resolve_forward_chat_id
            forward_chat_id = await resolve_forward_chat_id(PyroConf.FORWARD_CHAT_ID)
        except: pass

async def start_services():
    # 1. Thread ko sabse pehle start karo taaki Render turant Live ho jaye
    Thread(target=run_web, daemon=True).start()
    print("✅ Port 10000 par server start ho gaya hai.")

    await initialize()

    # 2. Login Sessions
    try:
        await user.start()
        LOGGER(__name__).info("User session online.")
    except Exception as e:
        LOGGER(__name__).error(f"User session fail: {e}")

    await app.start()
    print("🚀 Bot Running Successfully!")
    
    # 3. Keep Alive
    await asyncio.Event().wait()

# =======================
# MAIN ENTRY
# =======================
if __name__ == "__main__":
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start_services())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        LOGGER(__name__).error(f"Fatal Error: {e}")
    finally:
        LOGGER(__name__).info("Bot Stopped.")
        
