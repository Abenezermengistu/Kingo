import multiprocessing
import os
import time
import requests
from pathlib import Path

LOCK_FILE = Path("./telegram_bot.lock")
bot_process = None

def start_telegram_bot():
    global bot_process

    if LOCK_FILE.exists():
        print("Telegram bot is already running")
        return

    try:
        # Create the lock file
        LOCK_FILE.write_text("Telegram bot is running")

        # Start the bot process
        bot_process = multiprocessing.Process(target=run_bot)
        bot_process.start()
    except Exception as e:
        print(f"Error starting Telegram bot: {e}")
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()

def stop_telegram_bot(*args):
    global bot_process

    if bot_process is not None:
        bot_process.terminate()
        bot_process.join()
        bot_process = None

    if LOCK_FILE.exists():
        LOCK_FILE.unlink()

def check_internet_connection():
    url = "http://www.google.com"
    timeout = 30
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.ConnectionError:
        return False

def run_bot():
    import os
    import django
    import asyncio

    # Set the environment variable for Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kingo.settings')
    django.setup()  # Ensure Django is set up

    # Import your bot here after Django is set up
    from kingoapp import telegram_bot

    asyncio.run(telegram_bot.run_bot())  # Run the bot as a coroutine