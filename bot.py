import os
import time
import hmac
import hashlib
import requests
from urllib.parse import urlencode

from telegram import Update, BotCommand, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
API_KEY = os.getenv("BINANCE_API_KEY")
SECRET_KEY = os.getenv("BINANCE_SECRET_KEY")

WALLET_ADDRESS = "0x989a496a3d539e605e7513b8195221e100f76754"

# ---------------- DOCUMENT DATABASE ---------------- #

documents = {
    "1": {
        "name": "Interpreter",
        "file_path": "documents/interpreter.pdf",
        "price": 1
    },
    "2": {
        "name": "Pirates",
        "file_path": "documents/pirates.pdf",
        "price": 1
    },
    "3": {
        "name": "Wingdata",
        "file_path": "documents/wingdata.pdf",
        "price": 1
    },
}

user_state = {}
used_txids = set()

# ---------------- BINANCE VERIFY ---------------- #

def verify_txid(txid, required_amount):

    timestamp = int(time.time() * 1000)

    params = {
        "coin": "USDT",
        "status": 1,
        "timestamp": timestamp
    }

    query_string = urlencode(params)

    signature = hmac.new(
        SECRET_KEY.encode(),
        query_string.encode(),
        hashlib.sha256
    ).hexdigest()

    url = f"https://api.binance.com/sapi/v1/capital/deposit/hisrec?{query_string}&signature={signature}"

    headers = {"X-MBX-APIKEY": API_KEY}

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        return False

    deposits = r.json()

    for deposit in deposits:

        if deposit["txId"] == txid:

            if deposit["network"] == "BSC":

                if float(deposit["amount"]) >= required_amount:
                    return True

    return False


# ---------------- UI KEYBOARD ---------------- #

keyboard = [
    ["📄 Documents", "📊 Status"],
    ["ℹ Help"]
]

reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# ---------------- COMMANDS ---------------- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
Welcome to Document Store 📚

Steps to buy:
1️⃣ View documents
2️⃣ Select document
3️⃣ Send payment
4️⃣ Send TXID
5️⃣ Receive file
"""

    await update.message.reply_text(text, reply_markup=reply_markup)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = """
How to use:

1. Click 📄 Documents
2. Select document number
3. Send payment
4. Send TXID

Commands:
/start
/list
/status
/help
"""

    await update.message.reply_text(text)


async def list_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = "📄 Available Documents:\n\n"

    for doc_id, doc in documents.items():
        text += f"{doc_id}. {doc['name']} — {doc['price']} USDT\n"

    text += "\nReply with document number."

    await update.message.reply_text(text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = str(update.message.from_user.id)

    if user_id not in user_state:
        await update.message.reply_text("No active order.")
        return

    doc_id = user_state[user_id]["doc"]
    doc = documents[doc_id]

    await update.message.reply_text(
        f"Selected document:\n{doc['name']}\nPrice: {doc['price']} USDT"
    )


# ---------------- MESSAGE HANDLER ---------------- #

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = update.message.text.strip()
    user_id = str(update.message.from_user.id)

    if text == "📄 Documents":
        await list_docs(update, context)
        return

    if text == "📊 Status":
        await status(update, context)
        return

    if text == "ℹ Help":
        await help_command(update, context)
        return

    # selecting document
    if text in documents:

        user_state[user_id] = {"doc": text}

        doc = documents[text]

        await update.message.reply_text(
            f"Send {doc['price']} USDT (BEP20 BSC)\n\nWallet:\n{WALLET_ADDRESS}\n\nThen send TXID."
        )

        return

    # TXID
    if len(text) > 20:

        if user_id not in user_state:
            await update.message.reply_text("Select document first.")
            return

        doc_id = user_state[user_id]["doc"]
        doc = documents[doc_id]

        await update.message.reply_text("Checking payment...")

        if text in used_txids:
            await update.message.reply_text("Transaction already used.")
            return

        if verify_txid(text, doc["price"]):

            used_txids.add(text)

            with open(doc["file_path"], "rb") as f:
                await update.message.reply_document(f)

            await update.message.reply_text("Payment verified. Document sent.")

        else:

            await update.message.reply_text("Invalid transaction.")

        return

    await update.message.reply_text("Invalid input.")


# ---------------- COMMAND MENU ---------------- #

async def set_commands(app):

    commands = [
        BotCommand("start", "Start bot"),
        BotCommand("list", "View documents"),
        BotCommand("status", "Order status"),
        BotCommand("help", "Help")
    ]

    await app.bot.set_my_commands(commands)


# ---------------- RUN BOT ---------------- #

app = ApplicationBuilder().token(TOKEN).build()

app.post_init = set_commands

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("list", list_docs))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("status", status))

app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()