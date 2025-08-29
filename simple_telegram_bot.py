import telegram
from telegram.ext import Application, CommandHandler, ContextTypes

# Replace with your actual bot token from BotFather
TOKEN = "8444861913:AAHnuiL-INf6PttvBxgoSIKHMUjZvEYUDgM"

async def start(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text("你好！我是简单的搜索机器人。使用 /search [群组链接] [关键词] 来测试。")

async def search(update: telegram.Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /search command with basic response."""
    if not context.args or len(context.args) < 2:
        await update.message.reply_text("请提供群组链接和关键词，例如：/search https://t.me/groupname 关键词")
        return
    
    group_link = context.args[0]
    keyword = " ".join(context.args[1:])
    await update.message.reply_text(f"收到搜索请求！群组链接：{group_link}，关键词：{keyword}")

def main():
    """Run the bot."""
    application = Application.builder().token(TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("search", search))

    # Start the bot
    application.run_polling(allowed_updates=telegram.Update.ALL_TYPES)

if __name__ == "__main__":
    main()