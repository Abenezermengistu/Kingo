import os
import random
import string
import telebot
from telebot import types
import logging
from kingoapp.models import UserCustom
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from urllib.parse import urlencode

from telegram.constants import ParseMode
import random
from telegram import WebAppInfo
from django.conf import settings
import asyncio  # Import asyncio here

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kingo.settings')

import django
django.setup()  # Initialize Django here

from kingoapp.reg_func import register_user  # Import after Django initialization

API_TOKEN = "8158124024:AAF5GBpzsm6hfKt2PYaigVaZlvhLQKtHyac"  # Replace with your actual token
bot = telebot.TeleBot(API_TOKEN)

wallets = {}
registered_users = set()

image_path = os.path.join(settings.BASE_DIR, 'kingoapp', 'static', 'images', 'kingo.png')

if os.path.exists(image_path):
    with open(image_path, 'rb') as f:
        WELCOME_IMAGE = f.read()
else:
    raise FileNotFoundError(f"Image not found at: {image_path}")

def generate_random_string(length=6):
    """Generate a random string of lowercase letters and digits."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_user_wallet(telegram_user_id):
    from kingoapp.models import UserCustom  # Adjust this import to your app name

    try:
        user = UserCustom.objects.get(telegram_user_id=telegram_user_id)
        return {
            'balance': float(user.balance),
            'wins': user.wins,
            'losses': user.losses,
            'deposits': getattr(user, 'deposits', 0),
            'withdrawals': getattr(user, 'withdrawals', 0),
        }
    except UserCustom.DoesNotExist:
        return {
            "balance": 0,
            "wins": 0,
            "losses": 0,
            "deposits": 0,
            "withdrawals": 0,
        }

def build_main_menu():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🎲 Play", callback_data="play"),
        types.InlineKeyboardButton("📝 Register", callback_data="register"),
        types.InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
        types.InlineKeyboardButton("🏦 Deposit", callback_data="deposit"),
        types.InlineKeyboardButton("🛠️ Contact Support", callback_data="contact_support"),
        types.InlineKeyboardButton("📘 Instruction", callback_data="instruction"),
        types.InlineKeyboardButton("👥 Invite Friends", callback_data="invite")
    )
    return markup

@bot.message_handler(commands=["start"])
def start(message):
    bot.send_photo(
        message.chat.id,
        WELCOME_IMAGE,
        caption="🎉 *Welcome to Kingo!*\nChoose an option below.",
        parse_mode="Markdown"
    )
    bot.send_message(
        message.chat.id,
        "👇 *Main Menu:*",
        parse_mode="Markdown",
        reply_markup=build_main_menu()
    )

@bot.message_handler(commands=['register'])
def handle_register(message):
    chat_id = message.chat.id
    telegram_username = message.from_user.username or "N/A"  # Fallback in case it's None
    msg = bot.send_message(chat_id, "Enter your first name:")
    bot.register_next_step_handler(msg, get_first_name, telegram_username)

def get_first_name(message, telegram_username):
    first_name = message.text
    msg = bot.send_message(message.chat.id, "Enter your last name:")
    bot.register_next_step_handler(msg, get_last_name, first_name, telegram_username)

def get_last_name(message, first_name, telegram_username):
    last_name = message.text
    msg = bot.send_message(message.chat.id, "Please share your phone number:", reply_markup=phone_number_keyboard())
    bot.register_next_step_handler(msg, get_phone_number, first_name, last_name, telegram_username)

def phone_number_keyboard():
    """Creates a custom keyboard for sharing phone number."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("Share my contact", request_contact=True))
    return keyboard

def get_phone_number(message, first_name, last_name, telegram_username):
    if message.contact.user_id != message.from_user.id:
        bot.send_message(message.chat.id, "⚠️ Please share your own number.")
        return

    phone = message.contact.phone_number
    telegram_user_id = message.from_user.id
    rand = generate_random_string()

    username = f"user_{rand}"
    email = f"{rand}@nooglefit.com"
    password = generate_random_string(10)

    # Register the user with extra telegram fields
    success, msg_text = register_user(
        first_name, last_name, username, email, phone, password,
        telegram_user_id=telegram_user_id,
        telegram_username=telegram_username
    )

    if success:
        registered_users.add(message.from_user.id)
        bot.send_message(
            message.chat.id,
            f"🎉 Registered successfully!\nYour username is `{username}`.\nYou can now access your account on the platform.",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, f"❌ {msg_text}")

@bot.message_handler(content_types=["contact"])
def contact_handler(message):
    if message.contact.user_id != message.from_user.id:
        bot.send_message(message.chat.id, "⚠️ Please share your own number.")
        return

    user_id = message.from_user.id
    registered_users.add(user_id)

    bot.send_message(message.chat.id, f"✅ Thank you {message.from_user.first_name}, you are now registered!", reply_markup=types.ReplyKeyboardRemove())
    bot.send_photo(
        message.chat.id,
        WELCOME_IMAGE,
        caption="🎉 *Welcome to Kingo!*\nChoose an option below.",
        parse_mode="Markdown"
    )
    bot.send_message(
        message.chat.id,
        "👇 *Main Menu:*",
        parse_mode="Markdown",
        reply_markup=build_main_menu()
    )

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id
    telegram_username = call.from_user.username

    if call.data == "register":
        try:
            user = UserCustom.objects.get(telegram_user_id=user_id)
            bot.edit_message_text(f"✅ Welcome back, {telegram_username}!", call.message.chat.id, call.message.message_id)
        except UserCustom.DoesNotExist:
            handle_register(call.message)
        return

    # Check registration
    try:
        user = UserCustom.objects.get(telegram_user_id=user_id)
    except UserCustom.DoesNotExist:
        bot.answer_callback_query(call.id, "You must register first.")
        bot.edit_message_text("🚫 Please register using /register", call.message.chat.id, call.message.message_id)
        return


    if call.data == "play":
        wallet = get_user_wallet(user_id)
        if wallet is None:
            bot.edit_message_text("🚫 Please register or deposit first.", call.message.chat.id, call.message.message_id)
            return
    
        keyboard = InlineKeyboardMarkup(row_width=2)
    
        stake_buttons = []
        for stake in [10, 20, 50, 100]:
            query_params = urlencode({
                "user_id": user_id,
                "stake": stake,
                "wallet": round(wallet["balance"], 2)
            })
            webapp_url = f"https://abcreed2123.pythonanywhere.com?{query_params}"
            stake_buttons.append(InlineKeyboardButton(f"🎮 Play with ${stake}", web_app=WebAppInfo(url=webapp_url)))
    
        # Add stake buttons in 2-column layout
        for i in range(0, len(stake_buttons), 2):
            keyboard.add(*stake_buttons[i:i+2])
    
        # Add demo and back to menu buttons
        demo_url = f"https://abcreed2123.pythonanywhere.com?{urlencode({'user_id': user_id, 'stake': 0})}"
        keyboard.add(
            InlineKeyboardButton("🧪 Try Demo", web_app=WebAppInfo(url=demo_url)),
        )
    
        bot.edit_message_text(
            "💵 Choose a stake to launch the game:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=keyboard
        )
    elif call.data == "main_menu":
        bot.edit_message_text(
            "🏠 *Main Menu* - Choose an option below:",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            reply_markup=build_main_menu(),
            parse_mode="Markdown"
        )
    elif call.data == "check_balance":
        wallet = get_user_wallet(user_id)
        if wallet is None:
            bot.answer_callback_query(call.id, "⚠️ You're not registered yet.")
            return

        msg = (
            f"💼 *Your Wallet:*\n"
            f"Balance: ${wallet['balance']:.2f}\n"
            f"Wins: {wallet['wins']}\n"
            f"Losses: {wallet['losses']}\n"
            f"Deposits: ${wallet['deposits']}\n"
            f"Withdrawals: ${wallet['withdrawals']}"
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "deposit":
        msg = (
            "💳 *Deposit Instructions:*\n"
            "1. Send the amount to our account.\n"
            "2. Send payment proof to @KingoSupport.\n"
            "3. We'll update your balance shortly."
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
    elif call.data == "contact_support":
        bot.edit_message_text("🛠️ Contact @KingoSupport for help.", call.message.chat.id, call.message.message_id)

    elif call.data == "instruction":
        msg = (
            "📘 *How to Play Kingo:*\n"
            "1. Deposit funds\n"
            "2. Choose a stake\n"
            "3. Play and win!"
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")

    elif call.data == "invite":
        bot.edit_message_text(
            "📨 Share this bot: https://t.me/YourBotUsername?start=ref123",
            call.message.chat.id,
            call.message.message_id
        )

# === Run the Bot ===
async def run_bot():
    while True:
        try:
            await bot.polling(non_stop=True)
        except Exception as e:
            print(f"Error in bot polling: {e}")
            await asyncio.sleep(5)  # Wait before retrying

if __name__ == "__main__":
    asyncio.run(run_bot())  # Call the new run_bot function