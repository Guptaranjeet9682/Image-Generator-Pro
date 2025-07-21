from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackContext,
    CallbackQueryHandler
)
import requests
import os

# 🔐 Tokens and IDs from environment variables (Render setup)
TOKEN = os.getenv("TELEGRAM_TOKEN")
FORCE_JOIN_CHANNEL_ID = os.getenv("FORCE_JOIN_CHANNEL_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# 🧠 Memory storage
registered_users = set()

# ✅ Check if user joined the channel
def is_user_joined(user_id, context: CallbackContext):
    try:
        member = context.bot.get_chat_member(chat_id=FORCE_JOIN_CHANNEL_ID, user_id=user_id)
        return member.status in ["member", "creator", "administrator"]
    except:
        return False

# 🚀 /start command
def start(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    if not is_user_joined(user_id, context):
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/c/{FORCE_JOIN_CHANNEL_ID[4:]}")],
            [InlineKeyboardButton("✅ I Have Joined", callback_data="check_join")]
        ])
        update.message.reply_text(
            "🔒 Please join our channel to use this bot:",
            reply_markup=button
        )
        return

    registered_users.add(user_id)
    update.message.reply_text("✅ Welcome! Now send me any prompt and I’ll generate an image for you!")

# 🔁 Handle "I Have Joined" button
def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    user_id = query.from_user.id
    query.answer()

    if is_user_joined(user_id, context):
        registered_users.add(user_id)
        query.message.edit_text("✅ Access granted! Send your image prompt now.")
    else:
        query.answer("❗ You must join the channel first!", show_alert=True)

# 🎨 Image generation logic
def handle_prompt(update: Update, context: CallbackContext):
    user = update.effective_user
    user_id = user.id

    if not is_user_joined(user_id, context):
        update.message.reply_text("⚠️ Please use /start and join the channel first.")
        return

    prompt = update.message.text
    update.message.reply_text("🖼️ Generating image...")

    try:
        url = f"https://botfather.cloud/Apis/ImgGen/?prompt={prompt.replace(' ', '+')}"
        response = requests.get(url)
        if response.status_code == 200:
            update.message.reply_photo(photo=url, caption=f"🎨 Prompt: {prompt}")
        else:
            update.message.reply_text("❌ Failed to generate image. Try again later.")
    except Exception as e:
        update.message.reply_text(f"⚠️ Error: {e}")

# 🔐 Admin command to view users
def list_users(update: Update, context: CallbackContext):
    if update.effective_user.id != ADMIN_ID:
        return
    users = "\n".join([str(uid) for uid in registered_users]) or "No users yet."
    update.message.reply_text(f"📋 Registered Users:\n{users}")

# ▶️ Start the bot
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("users", list_users))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_prompt))
    dp.add_handler(MessageHandler(Filters.command, lambda u, c: None))
    dp.add_handler(CallbackQueryHandler(button_callback))

    updater.start_polling()
    print("✅ Bot is running...")
    updater.idle()

if __name__ == '__main__':
    main()
