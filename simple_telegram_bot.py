import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes
from telegram import Update
import re
import asyncio
from datetime import datetime

# Replace with your actual bot token from BotFather
TOKEN = "YOUR_BOT_TOKEN"

# In-memory storage for group messages (replace with SQLite for persistence)
GROUP_MESSAGES = {}  # {chat_id: [(message_id, text, timestamp), ...]}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text("你好！我是消息搜索机器人。使用 /search [群组或频道链接] [关键词] 搜索消息。\n注：仅支持公开频道或机器人加入后收到的群组消息。")

async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /search command to find messages in a group or channel."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("请提供群组或频道链接和关键词，例如：/search https://t.me/publicchannel 关键词")
        return

    # Extract link and keyword
    link = context.args[0]
    keyword = " ".join(context.args[1:])

    # Validate link format
    if not re.match(r"https://t.me/[a-zA-Z0-9_]+|https://t.me/\+[a-zA-Z0-9_-]+", link):
        await update.message.reply_text("无效的群组或频道链接，请提供有效的 Telegram 链接。")
        return

    try:
        # Resolve chat ID from link
        chat_id = await get_chat_id_from_link(link, context.bot)
        if not chat_id:
            await update.message.reply_text("无法解析链接，请确保链接有效且机器人可以访问。")
            return

        # Check if it's a public channel
        chat = await context.bot.get_chat(chat_id)
        is_public_channel = chat.type == "channel" and not getattr(chat, "is_private", False)

        messages = []
        if is_public_channel:
            # Fetch messages from public channel
            messages = await search_messages_in_chat(chat_id, keyword, context.bot)
        else:
            # For groups or private channels, search stored messages
            if str(chat_id) in GROUP_MESSAGES:
                messages = [
                    msg for msg_id, msg_text, _ in GROUP_MESSAGES[str(chat_id)]
                    if msg_text and keyword in msg_text
                ]
            else:
                await update.message.reply_text("机器人未在该群组或频道中收到消息，或需要管理员权限访问历史消息。")
                return

        if messages:
            response = "找到以下匹配的消息：\n"
            for msg in messages:
                # Construct message link
                prefix = "c/" if str(chat_id).startswith("-100") and not is_public_channel else ""
                message_link = f"https://t.me/{prefix}{str(chat_id).lstrip('-')}/{msg.message_id}"
                response += f"- {message_link}\n"
            await update.message.reply_text(response)
        else:
            await update.message.reply_text("未找到匹配关键词的消息。")
            
    except telegram.error.TelegramError as e:
        await update.message.reply_text(f"搜索时发生错误：{str(e)}")

async def get_chat_id_from_link(link: str, bot: telegram.Bot):
    """Resolve group/channel link to chat ID."""
    # Handle public (@username) or private (https://t.me/+invite) links
    username = link.split("t.me/")[-1]
    if username.startswith("+"):
        username = username[1:]  # Handle invite links
    else:
        username = "@" + username
    try:
        chat = await bot.get_chat(username)
        return chat.id
    except telegram.error.TelegramError:
        return None

async def search_messages_in_chat(chat_id: str, keyword: str, bot: telegram.Bot):
    """Search for messages in a public channel."""
    messages = []
    try:
        async for message in bot.get_chat_history(chat_id=chat_id, limit=100):
            if message.text and keyword in message.text:
                messages.append(message)
        return messages
    except telegram.error.TelegramError:
        return []

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Store incoming group messages for later searching."""
    if update.message and update.message.chat.type in ["group", "supergroup"]:
        chat_id = str(update.message.chat.id)
        if chat_id not in GROUP_MESSAGES:
            GROUP_MESSAGES[chat_id] = []
        GROUP_MESSAGES[chat_id].append((
            update.message.message_id,
            update.message.text,
            datetime.now()
        ))

def main():
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))
    # Add message handler for group messages (updated for v20+)
    application.add_handler(MessageHandler(
        telegram.ext.filters.TEXT & ~telegram.ext.filters.COMMAND & (
            telegram.ext.filters.ChatType.GROUPS | telegram.ext.filters.ChatType.SUPERGROUP
        ),
        handle_message
    ))

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
