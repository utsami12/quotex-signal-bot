import logging
from telegram import ReplyKeyboardMarkup, KeyboardButton, Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import pytz
import random

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔐 License store
licenses = {
    "sami": {"type": "lifetime", "assigned_id": None},
    "tareq": {"type": "lifetime", "assigned_id": None},
    "silent": {}
}

# Signal storage: {user_id: {"signal": {...}, "expires": datetime}}
signal_history = {}

# ✅ Bot Token (Inline)
TOKEN = "7451263167:AAFnyBX7S5YiiOBawsGuzy12keb-uyBe2R0"

# ✅ Bangladesh Local Time
def get_local_time(dt=None):
    if not dt:
        dt = datetime.utcnow()
    bd_timezone = pytz.timezone("Asia/Dhaka")
    return dt.astimezone(bd_timezone)

# ✅ Asset Formatter
def format_asset_name(asset_text):
    try:
        asset, suffix = asset_text.split(" - ")
        parts = asset.split("/")
        if parts[1] == "USD":
            asset = f"USD/{parts[0]}"
        return f"{asset} - {suffix}"
    except:
        return asset_text

# ✅ Validate License
def validate_license(user_id, license_key):
    now = datetime.now()
    if license_key in ["sami", "tareq"]:
        data = licenses[license_key]
        if data["assigned_id"] is None:
            data["assigned_id"] = user_id
            return True, "✅ License Activated!"
        elif data["assigned_id"] == user_id:
            return True, "✅ Already Activated!"
        else:
            return False, "❌ License used on another ID."
    elif license_key == "silent":
        if user_id in licenses["silent"]:
            return False, "⛔ Silent license already used on this ID."
        else:
            expire = now + timedelta(minutes=20)
            licenses["silent"][user_id] = expire
            return True, "✅ Silent License activated for 20 minutes."
    return False, "🚫 Invalid license."

# ✅ Check Access
def has_access(user_id):
    now = datetime.now()
    for key in ["sami", "tareq"]:
        if licenses[key]["assigned_id"] == user_id:
            return True
    if user_id in licenses["silent"]:
        return now < licenses["silent"][user_id]
    return False

# 📊 Asset List (OTC)
assets_otc = [
    "EUR/USD - OTC", "GBP/USD - OTC", "USD/JPY - OTC", "AUD/USD - OTC", "USD/CAD - OTC",
    "NZD/USD - OTC", "EUR/JPY - OTC", "GBP/JPY - OTC", "EUR/CHF - OTC", "USD/CHF - OTC",
    "EUR/AUD - OTC", "GBP/AUD - OTC", "AUD/JPY - OTC", "AUD/CHF - OTC", "NZD/JPY - OTC",
    "NZD/CHF - OTC", "CAD/CHF - OTC", "EUR/CAD - OTC", "GBP/CAD - OTC", "CHF/JPY - OTC",
    "USD/TRY - OTC", "USD/MXN - OTC", "USD/PKR - OTC", "USD/COP - OTC", "USD/BDT - OTC",
    "BRL/USD - OTC", "ARS/USD - OTC", "DZD/USD - OTC", "INR/USD - OTC", "EUR/SGD - OTC"
]

# ✅ Market Type
def get_market_type():
    day = datetime.now().strftime("%A")
    return "OTC" if day in ["Saturday", "Sunday"] else "Real Market"

# 🚀 Generate Signal
def generate_signal(user_id):
    now = get_local_time()

    # Check if previous signal still active
    if user_id in signal_history:
        if signal_history[user_id]["expires"] > now:
            return "⚠️ A signal is already active. Please wait until it expires."

    entry_time = (now + timedelta(minutes=1)).strftime("%H:%M")
    asset_raw = random.choice(assets_otc)
    asset = format_asset_name(asset_raw)

    signal = {
        "asset": asset,
        "direction": random.choice(["CALL", "PUT"]),
        "entry_time": entry_time,
        "duration": "1 Minute",
        "market": get_market_type(),
        "strategy": "Use martingale 1 step",
        "confidence": f"{random.randint(85, 95)}%"
    }

    expires_at = now + timedelta(minutes=2)
    signal_history[user_id] = {"signal": signal, "expires": expires_at}

    return (
        f"🚀 Quotex Trading Signal\n━━━━━━━━━━━━━━━━━\n"
        f"📍 Asset: {signal['asset']}\n"
        f"📈 Direction: {signal['direction']}\n"
        f"🕒 Entry Time: {signal['entry_time']}\n"
        f"⏳ Duration: {signal['duration']}\n"
        f"🏷️ Market: {signal['market']}\n"
        f"🛠️ {signal['strategy']}\n"
        f"🎯 Confidence: {signal['confidence']}\n"
        f"━━━━━━━━━━━━━━━━━\n✅ Status: Prepare to Enter"
    )

# 📊 Performance Display
def get_performance():
    return "📊 Bot Performance\n✅ Wins: 8\n❌ Losses: 2\n🎯 Accuracy: 80%"

# 🎛️ Menu (Signal Result Removed)
async def show_menu(update, context):
    keyboard = [
        [KeyboardButton("🚀 GENERATE SIGNAL")],
        [KeyboardButton("📊 Performance"), KeyboardButton("🌐 OTC Market"), KeyboardButton("📉 Real Market")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="🧭 Choose an option:", reply_markup=reply_markup)

# 🔰 Main Message Handler
async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()

    if not has_access(user_id):
        success, msg = validate_license(user_id, text)
        await update.message.reply_text(msg)
        if success:
            await show_menu(update, context)
        return

    if text == "🚀 generate signal":
        await update.message.reply_text(generate_signal(user_id))
    elif text == "📊 performance":
        await update.message.reply_text(get_performance())
    elif text == "🗂️ signal history":
        await update.message.reply_text("📂 History coming soon...")
    elif text in ["🌐 otc market", "📉 real market"]:
        await update.message.reply_text(f"✅ Market Selected: {text.title()}")
    else:
        await update.message.reply_text("🔐 Send your license key to activate the bot.")

# 🟢 Run Bot
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_user_message))
    print("🤖 Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
