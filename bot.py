import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("8798895118:AAGHXx_PuEvFzlBgU5cZYx6EJnXTbbTmwrg")

documents = {
    "1": {"name": "Sample PDF", "file": "https://example.com/sample.pdf", "price": "1$"}
}

user_state = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome!\nUse /list to see available documents.")

async def list_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Available Documents:\n"
    for key, doc in documents.items():
        text += f"{key}. {doc['name']} - {doc['price']} USDT\n"
    text += "\nReply with document number."
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.message.from_user.id)
    text = update.message.text.strip()

    if text in documents:
        user_state[user_id] = {"doc": text}
        await update.message.reply_text(
            f"Send 10 USDT to:\nYOUR_WALLET_ADDRESS\n\nThen send transaction ID."
        )
    elif len(text) > 20:  # assume TXID
        await update.message.reply_text("Checking transaction...")

        # TODO: Add Binance verification here
        await update.message.reply_text("Payment verified! Sending document...")

        doc = documents[user_state[user_id]["doc"]]
        await update.message.reply_text(doc["file"])
    else:
        await update.message.reply_text("Invalid input.")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("list", list_docs))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

app.run_polling()
