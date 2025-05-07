import uuid
from types import SimpleNamespace
from yookassa import Payment, Configuration
from settings.config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY, TIME


class YooKassaClient:
    def __init__(self):
        Configuration.account_id = YOOKASSA_SHOP_ID
        Configuration.secret_key = YOOKASSA_SECRET_KEY

    def create_payment(self, amount: float, subscription_type: str, **kwargs) -> SimpleNamespace:
        """
        Create payment in Yookassa

        :param amount: Summ
        :param subscription_type: Duration
        :return: Словарь с информацией о платеже
        """

        metadata = {"subscription_type": subscription_type}
        metadata.update({key: value for key, value in kwargs.items() if value is not None})
        payment = Payment.create(
            {
                "amount": {
                    "value": f"{amount:.2f}",
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "https://t.me/BestRealityVpnBot",
                },
                "capture": True,
                "description": f"Подписка для пользователя {metadata.get('user_id')} на Туннелирования приватного трафика: {TIME[subscription_type]}",
                "metadata": metadata,
                "receipt": {
                    "customer": {
                        "email": f"{metadata.get('user_email')}"
                    },
                    "items": [
                        {
                            "description": f"Подписка для пользователя {metadata.get('user_id')} на Туннелирования приватного трафика: {TIME[subscription_type]}",
                            "quantity": "1",
                            "amount": {
                                "value": f"{amount:.2f}",
                                "currency": "RUB"
                            },
                            "vat_code": 1
                        }
                    ]
                }
            },
            str(uuid.uuid4()),
        )

        data = SimpleNamespace(
            payment_id=payment.id,
            confirmation_url=payment.confirmation.confirmation_url
        )

        return data

    def check_payment_status(self, payment_id: str) -> SimpleNamespace:
        """
        Проверка статуса платежа в YooKassa.

        :param payment_id: ID платежа
        :return: Словарь с информацией о платеже
        """
        payment = Payment.find_one(payment_id)
        return SimpleNamespace(
            status=payment.status,
            user_id=payment.metadata.get("user_id"),
            subscription_type=payment.metadata.get("subscription_type"),
            server=payment.metadata.get("server"),
            chat_id=payment.metadata.get("chat_id"),
            message_id=payment.metadata.get("message_id"),
        )
