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

# Simple in-memory store — swap for a DB in production
members = {}

# VIP tiers (points-based loyalty — no gambling)
TIERS = {
    "starter":  {"min": 0,    "daily": 5,  "perk": "Welcome badge"},
    "bronze":   {"min": 100,  "daily": 10, "perk": "Bronze badge + 10 daily points"},
    "silver":   {"min": 500,  "daily": 20, "perk": "Silver badge + 20 daily points"},
    "gold":     {"min": 1500, "daily": 35, "perk": "Gold badge + 35 daily points"},
    "platinum": {"min": 5000, "daily": 50, "perk": "Platinum badge + 50 daily points"},
}


def get_tier(points: int) -> str:
    tier = "starter"
    for name, info in TIERS.items():
        if points >= info["min"]:
            tier = name
    return tier


def get_daily(points: int) -> int:
    return TIERS[get_tier(points)]["daily"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    members.setdefault(uid, {"points": 0, "last_bonus": None})

    keyboard = [
        [InlineKeyboardButton("🎁 Claim Daily Bonus", callback_data="bonus")],
        [InlineKeyboardButton("🏆 My VIP Tier", callback_data="tier")],
        [InlineKeyboardButton("📊 My Points", callback_data="points")],
        [InlineKeyboardButton("✨ View Perks", callback_data="perks")],
    ]
    await update.message.reply_text(
        "🎁 *Welcome to VIP Bonus Bot!*\n\n"
        "Claim daily bonuses, earn loyalty points, and unlock exclusive VIP perks — "
        "all right here in Telegram.\n\n"
        "Pick an option below 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    uid = q.from_user.id
    data = members.setdefault(uid, {"points": 0, "last_bonus": None})

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

        reward = get_daily(data["points"])
        data["points"] += reward
        data["last_bonus"] = now
        await q.edit_message_text(
            f"🎉 *Daily Bonus Claimed!*\n\n"
            f"+{reward} points added.\n"
            f"Total: *{data['points']}* points\n"
            f"VIP Tier: *{get_tier(data['points']).upper()}*",
            parse_mode="Markdown",
        )
    elif q.data == "tier":
        tier = get_tier(data["points"])
        await q.edit_message_text(
            f"🏆 Your VIP Tier: *{tier.upper()}*\n\n"
            f"Perk: {TIERS[tier]['perk']}",
            parse_mode="Markdown",
        )
    elif q.data == "points":
        nxt = next((t["min"] for t in TIERS.values() if t["min"] > data["points"]), None)
        nxt_txt = f"Next tier at *{nxt}* points." if nxt else "You've reached the top tier! 🎉"
        await q.edit_message_text(
            f"📊 You have *{data['points']}* points.\n{nxt_txt}",
            parse_mode="Markdown",
        )
    elif q.data == "perks":
        lines = [f"• *{n.upper()}* ({i['min']}+ pts): {i['perk']}" for n, i in TIERS.items()]
        await q.edit_message_text(
            "✨ *VIP Perks*\n\n" + "\n".join(lines),
            parse_mode="Markdown",
        )


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN environment variable is missing!")
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    logger.info("VIP Bonus Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
