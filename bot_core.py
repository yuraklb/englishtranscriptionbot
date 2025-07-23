#!/usr/bin/env python
# pylint: disable=unused-argument
"""Telegram bot for transcription"""
import logging
import os
import threading
import time
import requests
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

#TELEGRAM PART START
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

# TELEGRAM PART END

app = Flask(__name__)
INCOMING_HTTP_PORT = int(os.environ.get("INCOMING_HTTP_PORT", 8000))  # для Render или Railway

@app.route("/echo", methods=["POST"])
def echo_http():
    """echo"""
    data = request.data.decode("utf-8")
    print(f"[HTTP] Получено: {data}")
    return f"Вы отправили: {data}", 200

def http_server() -> None:
    """http_server"""
    # Запуск HTTP-сервера Flask
    print(f"[HTTP] Flask-сервер запущен на порту {INCOMING_HTTP_PORT}")
    app.run(host="0.0.0.0", port=INCOMING_HTTP_PORT)


#HTTP CLIENT

DESTINATION_HTTP_PORT = int(os.environ.get("DESTINATION_HTTP_PORT", 8000))
# SERVER_URL = os.environ.get("SERVER_URL", "http://localhost:")
DESTINATION_ADDRESS = f"http://localhost:{DESTINATION_HTTP_PORT}/echo"

def http_ping():
    """http_ping"""
    count = 1
    while True:
        time.sleep(10)
        message = f"Запрос номер {count}"
        try:
            response = requests.post(DESTINATION_ADDRESS, data=message.encode("utf-8"), timeout=100)
            print(f"[{count}] Ответ от сервера: {response.text}")
        except requests.RequestException as e:
            print(f"[{count}] Ошибка запроса: {e}")
        count += 1
        time.sleep(10)


def main() -> None:
    """Start the bot."""
    # Start server in separate thread. Render scan opened port.
    server_thread = threading.Thread(target=http_server, daemon=True)
    server_thread.start()

    http_ping_thread = threading.Thread(target=http_ping, daemon=True)
    http_ping_thread.start()


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
  