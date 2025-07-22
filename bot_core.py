#!/usr/bin/env python
# pylint: disable=unused-argument
"""Telegram bot for transcription"""
import logging
import os
import socket
import threading
import requests


from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"

TOKEN = os.getenv("TELEGRAM_API_KEY")

def get_transcription(word) :
    """Get transcription from external API"""
    url = API_URL.format(word.lower())
    try:
        res = requests.get(url)
        data = res.json()
        if isinstance(data, list):
            phonetics = data[0].get("phonetics", [])
            for p in phonetics:
                if "text" in p:
                    return p["text"]
        return "❌ Транскрипция не найдена."
    except Exception as e:
        return f"⚠️ Ошибка: {str(e)}"

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for incoming request"""
    text = update.message.text.strip()
    if not text.isalpha() or " " in text:
        await update.message.reply_text("Пожалуйста, введите одно английское слово.")
        return
    
    transcription = get_transcription(text)
    await update.message.reply_text(f"📖 Слово: *{text}*\n🔤 Транскрипция: `{transcription}`", parse_mode="Markdown")

def socket_server():
    port_number = 2222
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(("0.0.0.0", port_number))
    server_socket.listen()

    logger.info("Server listening port %d", port_number)

    while True:
        client_socket, addr = server_socket.accept()
        logger.info("Connecting from %s", addr)
        data = client_socket.recv(1024)
        print(f"Received: {data.decode()}")
        client_socket.sendall(data)
        client_socket.close()

    
def main() -> None:
    """Start the bot."""
    # Start server in separate thread. Render scan opened port.
    server_thread = threading.Thread(target=socket_server, daemon=True)
    server_thread.start()

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    # on different commands - answer in Telegram
    # application.add_handler(CommandHandler("start", start))
    # application.add_handler(CommandHandler("help", help_command))

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    logger.info("Start bot")

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
