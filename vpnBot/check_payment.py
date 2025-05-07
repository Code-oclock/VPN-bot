import asyncio

from flask import Flask, request, Response, jsonify
from settings.config import SUBSCRIPTION_DURATION, ALLOWED_IPS
import ipaddress
from clients.telegram_service import TelegramService
from clients.yookassa_client import YooKassaClient
from clients.xui_client import XUIClient

xui_client = XUIClient("settings/servers.json")
yookssClnt = YooKassaClient()

app = Flask(__name__)

def is_valid_ip(ip):
    for allowed_ip in ALLOWED_IPS:
        if ipaddress.ip_address(ip) in ipaddress.ip_network(allowed_ip, strict=False):
            return True
    return False

def setup_xui():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(xui_client.login_all())
    finally:
        loop.close()

setup_xui()

async def async_webhook_handler():
    try:
        data = request.json
        event = data.get("event")
        payment_id = data.get("object", {}).get("id")

        if event != "payment.succeeded":
            return Response(status=200)

        payment = yookssClnt.check_payment_status(payment_id)
        user_id = int(payment.user_id)
        server = payment.server
        duration = SUBSCRIPTION_DURATION[payment.subscription_type]

        status = await xui_client.get_subscription_status(user_id)

        if status and server in status:
            await xui_client.renew_subscription(user_id, duration, server)
            message = "✅ Ваша подписка успешно продлена!"
        else:
            connection_str = await xui_client.create_client(user_id, duration, server)
            message = f"✅ Оплата успешна!\nКонфигурация:\n`{connection_str}`"

        keyboard = {"inline_keyboard": [[{"text": "🏠 В главное меню", "callback_data": "main_menu"}]]}

        TelegramService.edit_message(
            chat_id=payment.chat_id,
            message_id=payment.message_id,
            text=message,
            reply_markup=keyboard,
        )

        return Response(status=200)

    except Exception as e:
        return Response(status=500)


async def cryptocloud_webhook():
    status = request.form.get('status')

    if status != "success":
        message = "Что-то пошло не так...(\nЕсли вы уверены, что оплата прошла, напишите в поддержку"
        # TODO
        # BOt send in supportChat WTF?
    else:
        order_id = request.form.get('order_id')
        parts = order_id.split(':')
        user_id = int(parts[1])
        server = parts[2]
        subscription_type = parts[3]
        chat_id = parts[4]
        message_id = parts[5]
        duration = SUBSCRIPTION_DURATION[subscription_type]
        status = await xui_client.get_subscription_status(user_id)

        if status and server in status:
            await xui_client.renew_subscription(user_id, duration, server)
            message = "✅ Ваша подписка успешно продлена!"
        else:
            connection_str = await xui_client.create_client(user_id, duration, server)
            message = f"✅ Оплата успешна!\nКонфигурация:\n`{connection_str}`"

        keyboard = {"inline_keyboard": [[{"text": "🏠 В главное меню", "callback_data": "main_menu"}]]}

        TelegramService.edit_message(
            chat_id=chat_id,
            message_id=message_id,
            text=message,
            reply_markup=keyboard,
        )

    return jsonify({"status": "success"}), 200


@app.route("/yookassa-webhook", methods=["POST"])
def handle_yookassa_webhook():
    if not is_valid_ip(request.remote_addr):
        return Response(status=403)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(async_webhook_handler())
    finally:
        loop.close()


@app.route("/cryptocloud-webhook", methods=["POST"])
def handle_cryptocloud_webhook():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(cryptocloud_webhook())
    finally:
        loop.close()


if __name__ == "__main__":
    app.run(host="45.129.242.138", port=8443, ssl_context='adhoc') # Для тестирования можно использовать самоподписанный сертификат ssl_context='adhoc'
    # from waitress import serve
    # serve(app, host="127.0.0.1", port=5000)
