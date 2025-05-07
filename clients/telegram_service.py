import requests
from settings.config import TG_BOT_TOKEN

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/"

class TelegramService:
    @staticmethod
    def edit_message(chat_id, message_id, text, reply_markup=None, parse_mode="Markdown"):
        url = TELEGRAM_API_URL + "editMessageText"
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": parse_mode,
            "reply_markup": reply_markup,
        }
        response = requests.post(url, json=payload)
        return response
