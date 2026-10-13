import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("👋 Hello! I'm your multipurpose bot.")

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()

if __name__ == "__main__":
    main()
