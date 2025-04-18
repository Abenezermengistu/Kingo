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
user_data = {}  # To store temporary data per user during withdrawal

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
        types.InlineKeyboardButton("🛠 Contact Support", callback_data="contact_support"),
        types.InlineKeyboardButton("📘 Instruction", callback_data="instruction"),
        types.InlineKeyboardButton("👥 Invite Friends", callback_data="invite"),
        types.InlineKeyboardButton("➕ More", callback_data="more")
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

    # Ensure user is registered
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

        available_balance = round(wallet["balance"], 2)
        keyboard = InlineKeyboardMarkup(row_width=2)
        stake_buttons = []

        for stake in [10, 20, 50, 100]:
            if available_balance >= stake:
                query_params = urlencode({
                    "user_id": user_id,
                    "stake": stake,
                    "wallet": available_balance
                })
                webapp_url = f"https://abcreed2123.pythonanywhere.com?{query_params}"
                stake_buttons.append(InlineKeyboardButton(f"🎮 Play with ${stake}", web_app=WebAppInfo(url=webapp_url)))

        for i in range(0, len(stake_buttons), 2):
            keyboard.add(*stake_buttons[i:i+2])

        demo_url = f"https://abcreed2123.pythonanywhere.com?{urlencode({'user_id': user_id, 'stake': 0})}"
        keyboard.add(
            InlineKeyboardButton("🧪 Try Demo", web_app=WebAppInfo(url=demo_url)),
        )

        if not stake_buttons:
            message = (
                f"😢 You don't have enough balance to play.\n"
                f"💸 Current Balance: ${available_balance:.2f}\n"
                f"🔋 Top up and come back to play!"
            )
            bot.edit_message_text(message, chat_id=call.message.chat.id, message_id=call.message.message_id)
            return

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

        # Retrieve total withdrawals from the wallet
        total_withdrawals = wallet.get('withdrawals', 0)

        msg = (
            f"💼 *Your Wallet:*\n"
            f"Balance: ${wallet['balance']:.2f}\n"
            f"Wins: {wallet['wins']}\n"
            f"Losses: {wallet['losses']}\n"
            f"Deposits: ${wallet['deposits']:.2f}\n"
            f"Withdrawals: ${total_withdrawals:.2f}"  # Display total withdrawals
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

    elif call.data == "withdraw":
        msg = "💰 Please enter the amount you want to withdraw:"
        bot.send_message(call.message.chat.id, msg)
        bot.register_next_step_handler(call.message, handle_withdraw_amount, user)

    elif call.data == "more":
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🏧 Withdraw", callback_data="withdraw"))
        bot.edit_message_text("🔍 More options available:", call.message.chat.id, call.message.message_id, reply_markup=markup)

    elif call.data == "bank_telebirr" or call.data == "bank_cbe":
        bank = "Telebirr" if call.data == "bank_telebirr" else "CBE Birr"
        if call.from_user.id not in user_data:
            user_data[call.from_user.id] = {}
        user_data[call.from_user.id]["bank"] = bank
        bot.send_message(call.message.chat.id, f"👤 Please enter account holder name for {bank}:")
        bot.register_next_step_handler(call.message, handle_account_name)

    elif call.data == "confirm_withdraw":
        confirm_or_cancel_withdraw(call, confirm=True)

    elif call.data == "cancel_withdraw":
        confirm_or_cancel_withdraw(call, confirm=False)

    elif call.data.startswith("withdraw_done:"):
        # Extract user_id and amount from callback_data
        _, target_user_id, withdrawn_amount = call.data.split(":")
        target_user_id = int(target_user_id)
        withdrawn_amount = float(withdrawn_amount)  # Convert to float

        # Get the user's wallet again to show updated data
        wallet = get_user_wallet(target_user_id)
        if wallet is None:
            bot.answer_callback_query(call.id, "⚠️ User not found.")
            return

        # Send confirmation to user
        bot.send_message(
            target_user_id,
            "✅ Please check your account. It has been credited."
        )

        # Send updated wallet info to admin (optional)
        msg = (
            f"✅ Withdrawal Completed!\n\n"
            f"💼 *User Wallet:*\n"
            f"Balance: ${wallet['balance']:.2f}\n"
            f"Wins: {wallet['wins']}\n"
            f"Losses: {wallet['losses']}\n"
            f"Deposits: ${wallet['deposits']:.2f}\n"
            f"Withdrawals: ${wallet['withdrawals']:.2f}\n"
            f"💵 Current Withdrawn Amount: ${withdrawn_amount:.2f}"
        )
        bot.edit_message_text(msg, call.message.chat.id, call.message.message_id, parse_mode="Markdown")
        
def handle_withdraw_amount(message, user):
    try:
        amount = float(message.text.strip())
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Check if user has sufficient balance
        wallet = get_user_wallet(user.telegram_user_id)
        if amount > wallet['balance']:
            bot.send_message(message.chat.id, "❌ Insufficient balance for this withdrawal. Please enter a different amount:")
            bot.register_next_step_handler(message, handle_withdraw_amount, user)
            return

        # Store amount in user_data
        if message.from_user.id not in user_data:
            user_data[message.from_user.id] = {}
        user_data[message.from_user.id]['amount'] = amount

        # Ask for bank selection
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("Telebirr", callback_data="bank_telebirr"),
            InlineKeyboardButton("CBE Birr", callback_data="bank_cbe"),
            InlineKeyboardButton("Cancel", callback_data="cancel_withdraw")
        )
        bot.send_message(
            message.chat.id,
            f"💵 Withdrawal Amount: ${amount:.2f}\n"
            "🏦 Select payment method:",
            reply_markup=markup
        )

    except ValueError:
        bot.send_message(message.chat.id, "❌ Invalid amount. Please enter a valid positive number:")
        bot.register_next_step_handler(message, handle_withdraw_amount, user)
        return

def handle_account_name(message):
    user_id = message.from_user.id
    account_name = message.text.strip()
    
    if not account_name or len(account_name) < 3:
        bot.send_message(message.chat.id, "❌ Invalid account name. Please enter a valid name.")
        bot.register_next_step_handler(message, handle_account_name)
        return
        
    user_data[user_id]['account_name'] = account_name
    
    # Ask for account number
    bot.send_message(message.chat.id, "🔢 Please enter your account number:")
    bot.register_next_step_handler(message, handle_account_number)
    return

def handle_account_number(message):
    user_id = message.from_user.id
    account_number = message.text.strip()

    # Validate that user_data contains the required keys
    if user_id not in user_data or 'amount' not in user_data[user_id]:
        bot.send_message(message.chat.id, "❌ Withdrawal session expired. Please start over.")
        return

    bank = user_data.get(user_id, {}).get("bank")

    if bank == "Telebirr":
        # Expecting a valid Ethiopian phone number (typically starts with 09 and is 10 digits)
        if not account_number.isdigit() or not account_number.startswith("09") or len(account_number) != 10:
            bot.send_message(message.chat.id, "❌ Invalid phone number. Please enter a valid 10-digit Telebirr number (e.g., 09XXXXXXXX).")
            bot.register_next_step_handler(message, handle_account_number)
            return
    elif bank == "CBE Birr":
        # CBE account numbers are typically at least 13 digits
        if not account_number.isdigit() or len(account_number) < 13:
            bot.send_message(message.chat.id, "❌ Invalid CBE account number. Please enter a valid numeric bank account number.")
            bot.register_next_step_handler(message, handle_account_number)
            return
    else:
        bot.send_message(message.chat.id, "⚠️ Bank type not recognized. Please start again.")
        return

    # Store the account number in user_data
    user_data[user_id]['account_number'] = account_number

    # Show confirmation
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("✅ Confirm Withdrawal", callback_data="confirm_withdraw"),
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_withdraw")
    )

    details = user_data[user_id]
    bot.send_message(
        message.chat.id,
        f"📋 Withdrawal Details:\n"
        f"💵 Amount: ${details['amount']:.2f}\n"
        f"🏦 Bank: {details['bank']}\n"
        f"👤 Account Name: {details['account_name']}\n"
        f"🔢 Account Number: {details['account_number']}\n\n"
        "Please confirm your withdrawal request:",
        reply_markup=markup
    )

from decimal import Decimal
from kingoapp.models import Withdrawal
from django.utils.timezone import now

ADMIN_CHAT_ID = 1487965128 

def confirm_or_cancel_withdraw(call, confirm):
    user_id = call.from_user.id

    if confirm:
        details = user_data.get(user_id, {})
        if not details:
            bot.edit_message_text(
                "❌ Withdrawal session expired. Please start over.",
                call.message.chat.id,
                call.message.message_id
            )
            return

        try:
            user = UserCustom.objects.get(telegram_user_id=user_id)
        except UserCustom.DoesNotExist:
            bot.send_message(call.message.chat.id, "❌ User not registered.")
            return

        amount = Decimal(str(details.get('amount', 0)))

        if user.balance >= amount > 0:
            # Update user balance and withdrawals
            user.balance -= amount
            user.withdrawals += amount  # Increment the total withdrawals
            user.save()  # Save the changes to the database

            # Save the withdrawal to the DB
            Withdrawal.objects.create(
                user=user,
                amount=amount,
                bank=details.get('bank'),
                account_name=details.get('account_name'),
                account_number=details.get('account_number'),
                created_at=now()
            )

            # Notify user
            bot.edit_message_text(
                "✅ Withdrawal request submitted!\n"
                "⏳ Processing time: within 24 hours\n"
                "📩 You'll receive a confirmation when completed.",
                call.message.chat.id,
                call.message.message_id
            )

            # Admin button to mark withdrawal as done
            done_button = InlineKeyboardMarkup()
            done_button.add(
                InlineKeyboardButton(
                    text="✅ Done",
                    callback_data=f"withdraw_done:{user_id}:{float(amount):.2f}"  # Include the amount in the callback_data
                )
            )

            # Notify admin
            user_data[user_id]['amount'] = float(amount)  # Ensure the amount is stored correctly
            bot.send_message(
                ADMIN_CHAT_ID,
                f"📤 *New Withdrawal Request:*\n"
                f"👤 User: @{call.from_user.username or 'N/A'} (`{call.from_user.id}`)\n"
                f"💵 Amount: `${amount:.2f}`\n"
                f"🏦 Bank: {details.get('bank')}\n"
                f"👤 Name: {details.get('account_name')}\n"
                f"🔢 Account: {details.get('account_number')}",
                parse_mode="Markdown",
                reply_markup=done_button
            )

        else:
            bot.send_message(call.message.chat.id, "❌ Insufficient balance or invalid amount.")
    else:
        bot.edit_message_text(
            "❌ Withdrawal cancelled.",
            call.message.chat.id,
            call.message.message_id
        )

    # Clear session data
    user_data.pop(user_id, None)
    
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