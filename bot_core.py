import os
from telegram.ext import Updater, MessageHandler, Filters
import requests

API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/{}"

TOKEN = os.getenv("TELEGRAM_API_KEY")

def get_transcription(word):
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

def handle(update, context):
    text = update.message.text.strip()
    if not text.isalpha() or " " in text:
        update.message.reply_text("Пожалуйста, введите одно английское слово.")
        return
    
    transcription = get_transcription(text)
    update.message.reply_text(f"📖 Слово: *{text}*\n🔤 Транскрипция: `{transcription}`", parse_mode="Markdown")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle))
    print("Бот запущен.")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
