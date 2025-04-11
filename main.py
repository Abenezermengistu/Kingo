import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ParseMode
import random
from telegram import WebAppInfo
# Store wallet info per user
wallets = {}

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

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define state for registration conversation
PHONE = 1

# A simple in-memory "database" to track registered users.
# In production, consider using a proper database.
registered_users = set()


WELCOME_IMAGE_URL = "kingo.png"  # Replace with your image URL

def build_main_menu() -> InlineKeyboardMarkup:
    """Builds the main menu with emoji-enhanced buttons."""
    keyboard = [
        [
            InlineKeyboardButton("🎲 Play", callback_data="play"),
            InlineKeyboardButton("📝 Register", callback_data="register"),
        ],
        [
            InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
            InlineKeyboardButton("🏦 Deposit", callback_data="deposit"),
        ],
        [
            InlineKeyboardButton("🛠️ Contact Support", callback_data="contact_support"),
            InlineKeyboardButton("📘 Instruction", callback_data="instruction"),
        ],
        [InlineKeyboardButton("👥 Invite Friends", callback_data="invite")],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the welcome image and main menu on /start."""
    chat_id = update.effective_chat.id

    # Send welcome image
    await context.bot.send_photo(
        chat_id=chat_id,
        photo=WELCOME_IMAGE_URL,
        caption="🎉 *Welcome to Kingo !*\nChoose an option below.",
        parse_mode=ParseMode.MARKDOWN
    )

    # Send menu with buttons
    await context.bot.send_message(
        chat_id=chat_id,
        text="👇 *Main Menu:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu()
    )

async def register_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the registration conversation by sending a phone number request."""
    user_id = update.effective_user.id

    if user_id in registered_users:
        await update.message.reply_text(
            "✅ You are already registered!",
            reply_markup=build_main_menu()
        )
        return ConversationHandler.END
    # Continue with registration flow if not registered
    # Create a custom keyboard with a contact request button
    keyboard = [
        [KeyboardButton("Share phone number", request_contact=True)]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True
    )
    await update.message.reply_text(
        "To complete your registration, please click the button below to share your phone number:",
        reply_markup=reply_markup,
    )
    return PHONE

async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receives the user's phone number and completes registration."""
    user = update.effective_user
    contact = update.message.contact

    if contact is None:
        await update.message.reply_text(
            "Please use the provided button to share your phone number."
        )
        return PHONE

    # Mark user as registered
    registered_users.add(user.id)

    # Send confirmation message
    await update.message.reply_text(
        f"✅ Thank you {user.first_name}, you are now registered!"
    )

    # Send welcome image and main menu again
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=WELCOME_IMAGE_URL,
        caption="🎉 *Welcome to Kingo !*\nChoose an option below.",
        parse_mode=ParseMode.MARKDOWN
    )

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="👇 *Main Menu:*",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu()
    )

    return ConversationHandler.END

async def play_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    if user.id not in registered_users:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(
            "🚫 You need to register first. Click /register to get started."
        )
        return

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        text="🍀 *Best of luck on your gaming adventure!* 🎮",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_play_menu()
    )

WELCOME_IMAGE_URL = "kingo.png"

async def send_main_menu(query, context):
    user = query.from_user
    chat_id = query.message.chat_id
    message_id = query.message.message_id

    # Delete previous message with photo
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception as e:
        print("Failed to delete message:", e)

    # Send a new message with text and menu
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🎉 *Welcome Back To Kingo , {user.first_name}!* 👇 Main Menu:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=build_main_menu()
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button presses from the inline keyboard."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    # If not registered and trying anything other than register
    if query.data != "register" and user_id not in registered_users:
        await query.edit_message_text("🚫 You need to register. Click /register to get started.")
        return


    if query.data == "register":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")]
        ])
        
        await query.message.edit_text("You are already registered.", reply_markup=keyboard)

        
    elif query.data == "play":
        await play_handler(update, context)

    elif query.data.startswith("play_"):
        amount = int(query.data.split("_")[1])
        wallet = get_user_wallet(user_id)

        if wallet["balance"] < amount:
            await query.edit_message_text(
                f"❌ Not enough balance to play with ${amount}. Please deposit first."
            )
        else:
            wallet["balance"] -= amount
            wallet["balance"] = round(wallet["balance"], 2)

            # Construct URL with parameters for Mini Web App
            base_url = "https://t.me/FitfusionEthiopiaBot/Kingo"
            url_with_params = f"{base_url}?wallet={wallet['balance']}&stake={amount}&user_id={user_id}"
    
            keyboard = InlineKeyboardMarkup([
                 [InlineKeyboardButton("▶️ Launch Game", web_app=WebAppInfo(url=url_with_params))],
                 [InlineKeyboardButton("🏠 Back to Menu", callback_data="main_menu")]
            ])

            await query.edit_message_text(
                text=(
                    f"✅ You have staked *${amount}*.\n"
                    f"💼 Remaining Wallet Balance: *${wallet['balance']}*\n\n"
                    f"Click below to start the game ⬇️"
                ),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=keyboard
            )


    elif query.data == "check_balance":
       wallet = get_user_wallet(user_id)
       back_button = InlineKeyboardMarkup([
           [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
       ])
       await query.edit_message_text(
           f"💼 *Your Wallet:*\n"
           f"Balance: ${wallet['balance']}\n"
           f"Wins: {wallet['wins']}\n"
           f"Losses: {wallet['losses']}\n"
           f"Deposited: ${wallet['deposits']}\n"
           f"Withdrawn: ${wallet['withdrawals']}",
           parse_mode=ParseMode.MARKDOWN,
           reply_markup=back_button
        )


    elif query.data == "deposit":
        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
    ])
        await query.edit_message_text(
            "💳 *Deposit Instructions:*\n"
            "1. Send the amount to our payment account.\n"
            "2. Once payment is complete, send proof to support.\n"
            "3. Your wallet will be updated shortly.\n\n"
            "For help, contact [Support](https://t.me/KingoSupport).",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button
        )

    elif query.data == "contact_support":
       back_button = InlineKeyboardMarkup([
           [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
       ])
       await query.edit_message_text(
           "🛠️ *Support Team:*\nFor help, contact [Kingo Support](https://t.me/KingoSupport)",
           parse_mode=ParseMode.MARKDOWN,
           reply_markup=back_button
    )

    elif query.data == "instruction":
        back_button = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")]
        ])
        await query.edit_message_text(
            "📜 *How to Play Kingo :*\n"
            "1. Deposit to your wallet.\n"
            "2. Choose a game amount.\n"
            "3. Mark numbers drawn until Bingo!\n"
            "4. Win cash prizes!\n\n"
            "🎯 *Try the demo game to practice!*",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=back_button
        )



    elif query.data == "invite":
        await query.edit_message_text(
            "📨 *Invite Friends:*\nShare this link: https://t.me/YourBotUsername?start=referral123",
            parse_mode=ParseMode.MARKDOWN,
        )
    elif query.data == "main_menu":
        await send_main_menu(query, context)
    

    else:
        await query.edit_message_text("Unknown option selected.")

async def deposit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    wallet = get_user_wallet(user.id)

    wallet["balance"] += 100  # Example amount
    wallet["deposits"] += 100

    await update.callback_query.answer()
    await update.callback_query.edit_message_text(
        f"✅ Deposit successful! Your new balance is: ${wallet['balance']}"
    )

def main() -> None:
    """Run the bot."""
    # Replace 'YOUR_TELEGRAM_BOT_TOKEN' with your bot's token.
    application = Application.builder().token("8158124024:AAF5GBpzsm6hfKt2PYaigVaZlvhLQKtHyac").build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    
    # Conversation handler for registration (phone sharing)
    reg_handler = ConversationHandler(
        entry_points=[CommandHandler("register", register_command)],
        states={
            PHONE: [MessageHandler(filters.CONTACT, receive_phone)],
        },
        fallbacks=[],
    )
    application.add_handler(reg_handler)
    
    # CallbackQuery handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # Start the bot
    application.run_polling()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo

def build_play_menu() -> InlineKeyboardMarkup:
    """Builds the play menu with stake amounts passed as URL parameters."""
    base_url = "https://bingo-telegram-bot-nu.vercel.app"  # Your base URL

    keyboard = [
        [
            InlineKeyboardButton("💵 Play with $10", web_app=WebAppInfo(url=f"{base_url}?stake=10")),
            InlineKeyboardButton("💵 Play with $20", web_app=WebAppInfo(url=f"{base_url}?stake=20")),
        ],
        [
            InlineKeyboardButton("💵 Play with $50", web_app=WebAppInfo(url=f"{base_url}?stake=50")),
            InlineKeyboardButton("💵 Play with $100", web_app=WebAppInfo(url=f"{base_url}?stake=100")),
        ],
        [InlineKeyboardButton("🎯 Try Demo Game", web_app=WebAppInfo(url=f"{base_url}?stake=0"))],
        [InlineKeyboardButton("🏠 Back to Main Menu", callback_data="main_menu")] 
    ]
    return InlineKeyboardMarkup(keyboard)


# Store user choices per game
user_choices = {}

async def select_number(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles user's number selection and ensures only one choice per game."""
    query = update.callback_query
    user_id = query.from_user.id
    chosen_number = int(query.data.split("_")[1])  # Example format: "number_5"

    # Check if the user already made a selection
    if user_id in user_choices:
        await query.answer("🚫 You have already chosen a number for this game!", show_alert=True)
        return

    # Save the user's choice
    user_choices[user_id] = chosen_number

    await query.answer(f"✅ You selected {chosen_number}.", show_alert=True)

    # (Optional) Notify the user of their selection
    await query.edit_message_text(
        text=f"🎯 You selected *{chosen_number}*.\nWait for the game results...",
        parse_mode=ParseMode.MARKDOWN
    )
def reset_game():
    """Clears user selections for a new round."""
    global user_choices
    user_choices = {}


if __name__ == "__main__":
    main()
