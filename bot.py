import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")

# In-memory store (swap with DB for production)
users = {}

VIP_TIERS = {
    "bronze":   {"min": 100,  "bonus": 5},
    "silver":   {"min": 500,  "bonus": 10},
    "gold":     {"min": 1000, "bonus": 20},
    "platinum": {"min": 5000, "bonus": 50},
}


def get_tier(points: int) -> str:
    tier = "none"
    for name, info in VIP_TIERS.items():
        if points >= info["min"]:
            tier = name
    return tier


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users.setdefault(uid, {"points": 0, "last_bonus": None})

    keyboard = [
        [InlineKeyboardButton("🎁 Claim Bonus", callback_data="bonus")],
        [InlineKeyboardButton("🏆 My VIP Tier", callback_data="tier")],
        [InlineKeyboardButton("📊 My Points", callback_data="points")],
    ]
    await update.message.reply_text(
        "🎁 *Welcome to VIP Bonus Bot!*\n\n"
        "Claim daily bonuses, earn points & unlock VIP rewards — right here in Telegram.\n\n"
        "Pick an option below 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = users.setdefault(uid, {"points": 0, "last_bonus": None})

    if q.data == "bonus":
        now = datetime.utcnow()
        last = data["last_bonus"]
        if last and now - last < timedelta(hours=24):
            wait = timedelta(hours=24) - (now - last)
            hrs, rem = divmod(wait.seconds, 3600)
            mins = rem // 60
            await q.edit_message_text(
                f"⏳ Bonus already claimed!\nCome back in *{hrs}h {mins}m*.",
                parse_mode="Markdown",
            )
            return

        tier = get_tier(data["points"])
        reward = VIP_TIERS.get(tier, {}).get("bonus", 5)
        data["points"] += reward
        data["last_bonus"] = now
        await q.edit_message_text(
            f"🎉 *Bonus Claimed!*\n\n+{reward} points added.\n"
            f"Total: *{data['points']}* points\n"
            f"Tier: *{get_tier(data['points']).upper()}*",
            parse_mode="Markdown",
        )
    elif q.data == "tier":
        await q.edit_message_text(
            f"🏆 Your VIP tier: *{get_tier(data['points']).upper()}*",
            parse_mode="Markdown",
        )
    elif q.data == "points":
        await q.edit_message_text(
            f"📊 You have *{data['points']}* points.",
            parse_mode="Markdown",
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing!")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("VIP Bonus Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
