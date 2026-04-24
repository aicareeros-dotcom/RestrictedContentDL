# Copyright (C) @TheSmartBisnu
# Final Render Fix with app.run() 🚀

import os
import asyncio
import logging
from threading import Thread
from flask import Flask
from logging.handlers import RotatingFileHandler

# ===== 1. LOGGER SETUP =====
try:
    if os.path.exists("logs.txt"):
        os.remove("logs.txt")
except:
    pass

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt="%d-%b-%y %I:%M:%S %p",
    handlers=[
        RotatingFileHandler("logs.txt", mode="w+", maxBytes=5000000, backupCount=10),
        logging.StreamHandler(),
    ],
)
LOGGER = logging.getLogger(__name__)

# ===== 2. FLASK SERVER (For Render Live Status) =====
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Bot is LIVE 🚀", 200

def run_web():
    # Port 10000 fixed for Render
    try:
        flask_app.run(host="0.0.0.0", port=10000, debug=False, use_reloader=False)
    except Exception as e:
        LOGGER.error(f"Flask Error: {e}")

# Web server ko background mein start kar rahe hain
Thread(target=run_web, daemon=True).start()

# ===== 3. BOT CLIENTS =====
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from config import PyroConf

# Aapka main bot client
app = Client(
    "media_bot",
    api_id=PyroConf.API_ID,
    api_hash=PyroConf.API_HASH,
    bot_token=PyroConf.BOT_TOKEN,
    workers=100,
    parse_mode=ParseMode.MARKDOWN
)

# Aapka user session client
user = Client(
    "user_session",
    api_id=PyroConf.API_ID,
    api_hash=PyroConf.API_HASH,
    session_string=PyroConf.SESSION_STRING
)

# ===== 4. COMMAND HANDLERS =====
@app.on_message(filters.command("start") & filters.private)
async def start_cmd(_, message):
    await message.reply("👋 **Bot is Online with app.run() on Render!**")

# ===== 5. STARTUP & RUN =====
async def initialize():
    # Yahan aap apni extra settings (like semaphore) add kar sakte hain
    LOGGER.info("Initializing services...")
    try:
        await user.start()
        LOGGER.info("✅ User session started!")
    except Exception as e:
        LOGGER.error(f"❌ User session failed: {e}")

if __name__ == "__main__":
    # Pehle initialize karenge, phir bot run karenge
    loop = asyncio.get_event_loop()
    loop.run_until_complete(initialize())
    
    LOGGER.info("🚀 Starting Bot with app.run()...")
    # Ye block karega aur bot ko chalta rakhega
    app.run()
    
