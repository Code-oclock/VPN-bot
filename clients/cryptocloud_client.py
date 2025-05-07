import uuid

import requests

from settings.config import CRYPTOCLOUD_API_KEY, CRYPTOCLOUD_SHOP_ID


class CryptocloudClient:
    @staticmethod
    async def create_cryptocloud_payment(user_id, price, server, subscription_type, chat_id, message_id):
        order_id = f"{uuid.uuid4()}:{user_id}:{server}:{subscription_type}:{chat_id}:{message_id}"
        url = "https://api.cryptocloud.plus/v2/invoice/create"
        headers = {
            "Authorization": f"Token {CRYPTOCLOUD_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "amount": str(price),
            "shop_id": CRYPTOCLOUD_SHOP_ID,
            "currency": "RUB",
            "order_id": order_id,
        }

        response = requests.post(url, json=data, headers=headers)
        print(response.text)
        print(response.json())

        if response.status_code == 200:
            return response.json()["result"]["link"]
        return ""