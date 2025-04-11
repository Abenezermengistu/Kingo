import os
import random
import string
import telebot
from telebot import types
from django.conf import settings
import asyncio  # Import asyncio here

# Set the environment variable for Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kingo.settings')

# Now import Django-related functions after the setup
import django
django.setup()  # Initialize Django here

from kingoapp.reg_func import register_user  # Import after Django initialization

# API Token for the Telegram Bot
API_TOKEN = "8158124024:AAF5GBpzsm6hfKt2PYaigVaZlvhLQKtHyac"  # Replace with your actual token
bot = telebot.TeleBot(API_TOKEN)

# In-Memory Stores
wallets = {}
registered_users = set()

# File path for the welcome image
image_path = os.path.join(settings.BASE_DIR, 'kingoapp', 'static', 'images', 'kingo.png')

# Check if the image exists and load it
if os.path.exists(image_path):
    with open(image_path, 'rb') as f:
        WELCOME_IMAGE = f.read()
else:
    raise FileNotFoundError(f"Image not found at: {image_path}")

def generate_random_string(length=6):
    """Generate a random string of lowercase letters and digits."""
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def get_user_wallet(user_id):
    if user_id not in wallets:
        wallets[user_id] = {
            "balance": 0,
            "wins": 0,
            "losses": 0,
            "deposits": 0,
            "withdrawals": 0,
        }
    return wallets[user_id]

# === Main Menu ===
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

# === Start Command ===
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

# === Register Command ===
@bot.message_handler(commands=['register'])
def handle_register(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, "Enter your first name:")
    bot.register_next_step_handler(msg, get_first_name)

def get_first_name(message):
    first_name = message.text
    msg = bot.send_message(message.chat.id, "Enter your last name:")
    bot.register_next_step_handler(msg, get_last_name, first_name)

def get_last_name(message, first_name):
    last_name = message.text
    msg = bot.send_message(message.chat.id, "Please share your phone number:", reply_markup=phone_number_keyboard())
    bot.register_next_step_handler(msg, get_phone_number, first_name, last_name)

def phone_number_keyboard():
    """Creates a custom keyboard for sharing phone number."""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(types.KeyboardButton("Share my contact", request_contact=True))
    return keyboard

def get_phone_number(message, first_name, last_name):
    if message.contact.user_id != message.from_user.id:
        bot.send_message(message.chat.id, "⚠️ Please share your own number.")
        return

    phone = message.contact.phone_number
    rand = generate_random_string()

    username = f"user_{rand}"
    email = f"{rand}@nooglefit.com"
    password = generate_random_string(10)

    # Register the user
    success, msg_text = register_user(first_name, last_name, username, email, phone, password)

    if success:
        registered_users.add(message.from_user.id)  # Mark the user as registered
        bot.send_message(
            message.chat.id,
            f"🎉 Registered successfully!\nYour username is `{username}`.\nYou can now access your account on the platform.",
            parse_mode="Markdown"
        )
    else:
        bot.send_message(message.chat.id, f"❌ {msg_text}")

# === Receive Phone Number ===
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

# === Callback Query Handler ===
@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    user_id = call.from_user.id

    if call.data != "register" and user_id not in registered_users:
        bot.answer_callback_query(call.id, "You must register first.")
        bot.edit_message_text("🚫 Please register using /register", call.message.chat.id, call.message.message_id)
        return

    if call.data == "register":
        if user_id in registered_users:
            bot.edit_message_text("✅ You are already registered!", call.message.chat.id, call.message.message_id)
        else:
            handle_register(call.message)  # Call the function directly for registration flow

    elif call.data == "play":
        play_menu = types.InlineKeyboardMarkup(row_width=2)
        play_menu.add(
            types.InlineKeyboardButton("💵 Play with $10", callback_data="play_10"),
            types.InlineKeyboardButton("💵 Play with $20", callback_data="play_20"),
            types.InlineKeyboardButton("💵 Play with $50", callback_data="play_50"),
            types.InlineKeyboardButton("💵 Play with $100", callback_data="play_100"),
            types.InlineKeyboardButton("🎯 Demo Game", callback_data="play_0"),
            types.InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")
        )
        bot.edit_message_text("Choose your stake amount:", call.message.chat.id, call.message.message_id, reply_markup=play_menu)

    elif call.data.startswith("play_"):
        amount = int(call.data.split("_")[1])
        wallet = get_user_wallet(user_id)

        if amount > 0 and wallet["balance"] < amount:
            bot.edit_message_text(f"❌ Not enough balance to play with ${amount}.", call.message.chat.id, call.message.message_id)
            return

        if amount > 0:
            wallet["balance"] -= amount

        launch_url = f"https://t.me/FitfusionEthiopiaBot/elite?user_id={user_id}&stake={amount}&wallet={wallet['balance']}"
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("▶️ Launch Game", url=launch_url))
        keyboard.add(types.InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu"))

        bot.edit_message_text(
            f"✅ Staked: ${amount}\n💼 Balance: ${wallet['balance']}\nTap below to play.",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=keyboard
        )

    elif call.data == "check_balance":
        wallet = get_user_wallet(user_id)
        msg = (
            f"💼 *Your Wallet:*\n"
            f"Balance: ${wallet['balance']}\n"
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