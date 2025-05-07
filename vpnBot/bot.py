import logging

from email_validator import validate_email, EmailNotValidError
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes, MessageHandler,
    filters, ConversationHandler
)

from clients.cryptocloud_client import CryptocloudClient
from settings.config import SUBSCRIPTION_PRICES, TG_BOT_TOKEN, TIME, SERVERS_NAMES, SUPPORT_LINK, MAX_CLIENTS
from clients.xui_client import XUIClient
from clients.yookassa_client import YooKassaClient

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
xui = XUIClient("settings/servers.json")
yooKassaClient = YooKassaClient()
cryptocloudClient = CryptocloudClient()
DEFAULT = "germany_1"

async def post_init(application):
    await xui.login_all()

def create_keyboard(buttons) -> InlineKeyboardMarkup:
    """
    Universal function for create keyboard
    :param buttons: List with buttons format:[["Text", is_url, "callback_data_or_url"]]
    :return: InlineKeyboardMarkup
    """
    keyboard = [
        [InlineKeyboardButton(text, url=data if is_url else None, callback_data=None if is_url else data)]
        for text, is_url, data in buttons
    ]
    return InlineKeyboardMarkup(keyboard)

async def count_price(range_price: dict, server: str) -> int:
    min_price = range_price[min]
    max_price = range_price[max]
    clients = await xui.get_list_of_users(server)
    different = round((max_price - min_price) * (len(clients) / MAX_CLIENTS))
    actual_price = max_price - different
    return actual_price


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main menu == /start
    :param update: ...
    :param context: ...
    :return: -
    """
    welcome_text = (
        "👋 Привет!\n\n"
        "Добро пожаловать в VPN бот! 🚀\n\n"
        "✅ Здесь ты можешь оформить подписку на надёжный VPN-сервис\n"
        "🌐 С моей помощью ты сможешь быстро и удобно получить доступ к защищённым серверам во Франции 🇫🇷, Германии 🇩🇪, Нидерланды 🇳🇱, Испания 🇪🇸\n"
        "⏳ Сроки подписки: от 1 дня до 6 месяцев\n\n"
        "Если у тебя возникли вопросы или проблемы, можешь открыть FAQ или написать в поддержку\n"
        "Удачи и безопасного серфинга в интернете! 🌐😊\n\n"
        "Выбери, что хочешь сделать:"
    )
    reply_markup = create_keyboard(
        [
            ["🛒 Новая подписка", False, "new_subscription"],
            ["📊 Статус подписки", False, "status"],
            ["🔄 Продлить подписку", False, "renew"],
            ["🆘 Поддержка", True, "https://t.me/RealityVPNSupportBot?start"],
            ["❓ FAQ", True, SUPPORT_LINK]
        ]
    )
    if update.message:
        await update.message.reply_text(
            welcome_text, reply_markup=reply_markup
        )
    else:
        await update.callback_query.edit_message_text(
            welcome_text, reply_markup=reply_markup
        )


async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["awaiting_email"] = True
    reply_markup = create_keyboard(
        [
            ["🏠 В главное меню", False, "main_menu"]
        ]
    )
    message = await update.message.reply_text("📩 Пожалуйста, отправьте ваш email для получения чека.",
                                              reply_markup=reply_markup)
    context.user_data["email_message_id"] = message.message_id
    context.user_data["email_chat_id"] = message.chat_id
    context.user_data["email_not_valid"] = False
    return 0


async def save_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_email"):
        return ConversationHandler.END

    email = update.message.text
    reply_markup = create_keyboard([["🏠 В главное меню", False, "main_menu"]])

    try:
        valid = validate_email(email)
        email = valid.normalized
        context.user_data["email"] = email

        await context.bot.edit_message_text(
            chat_id=context.user_data["email_chat_id"],
            message_id=context.user_data["email_message_id"],
            text=f"✅ Email сохранён: {email}",
            reply_markup=reply_markup
        )

        try:
            await update.message.delete()
        except Exception as e:
            logging.error(f"Ошибка при удалении сообщения: {e}")

        return ConversationHandler.END

    except EmailNotValidError as e:
        error_message = f"❌ Неверный email: {str(e)}\nПожалуйста, введите корректный email:"

        if not context.user_data["email_not_valid"]:
            await context.bot.edit_message_text(
                chat_id=context.user_data["email_chat_id"],
                message_id=context.user_data["email_message_id"],
                text=error_message,
                reply_markup=reply_markup
            )

        context.user_data["email_not_valid"] = True

        try:
            await update.message.delete()
        except Exception as e:
            logging.error(f"Ошибка при удалении сообщения: {e}")

        return 0


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle push button
    :param update: ...
    :param context: ...
    :return: -
    """
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data
    text = ""
    reply_markup = None

    if data == "main_menu":
        await start(update, context)
        context.user_data["awaiting_email"] = False
        return ConversationHandler.END


    if data == "coming_soon":
        return

    elif data == "status":
        status = await xui.get_subscription_status(user_id)
        if status:
            text = f"📊 Статус вашей подписки:\n\n"
            for server, server_data in status.items():
                text += (
                    f"🔒 Состояние: {'Активна ✅' if server_data['active'] else 'Неактивна ❌'}\n"
                    f"📅 Дата окончания: {server_data['expiry_date']}\n"
                    f"🌐 Сервер: {SERVERS_NAMES[server].capitalize()}\n\n"
                    f"🔑 Ключ:\n `{await xui.get_connection_string(server_data['id'], server_data['email'], server)}`\n\n"
                )
        else:
            text = "❌ У тебя пока нет активной подписки 😕"

        reply_markup = create_keyboard(
            [
                ["🏠 В главное меню", False, "main_menu"]
            ]
        )

    elif data == "faq":
        text = """
1) Если вы выбрали пункт 'новая подписка' на сервер, на котором подписка уже активна, то она автоматически продлится на оплаченный срок\n
2) Оформление закаказа лучше всгда начинать со /start. Для безопасности стандартными значениями является сервер во франции со срок подписки = 1 день.
        """

        reply_markup = create_keyboard(
            [
                ["🏠 В главное меню", False, "main_menu"]
            ]
        )

    elif data in ["new_subscription", "renew"]:
        
        context.user_data["subscription_mode"] = data

        text = "Выберите сервер:"
        reply_markup = create_keyboard([
            ["🇩🇪 Германия I", False, "server-germany_1" if len(await xui.get_list_of_users("germany_1")) <= MAX_CLIENTS else "full"],
            ["🇫🇷 Франция (🚫 coming soon)", False, "coming_soon"],
            ["🇳🇱 Нидерланды (🚫 coming soon)", False, "coming_soon"],
            ["🇪🇸 Испания (🚫 coming soon)", False, "coming_soon"],
            ["🏠 В главное меню", False, "main_menu"],
        ])

    elif data == "full":
        text = "Извините, текущий сервер пока не доступен"
        reply_markup = create_keyboard([
            ["🔙 Назад", False, context.user_data.get("subscription_mode", "new_subscription")],
        ])

    elif data.startswith("server-"):
        server = data.split("-")[1]

        context.user_data["server"] = server

        prices = {
            "1_day": await count_price(SUBSCRIPTION_PRICES['1_day'], server),
            "1_week": await count_price(SUBSCRIPTION_PRICES['1_week'], server),
            "1_month": await count_price(SUBSCRIPTION_PRICES['1_month'], server),
            "6_months": await count_price(SUBSCRIPTION_PRICES['6_months'], server)
        }

        reply_markup = create_keyboard([
            [f"1️⃣ 1 День - {prices['1_day']} руб", False, "1_day"],
            [f"🗓 1 Неделя - {prices['1_week']} руб", False, "1_week"],
            [f"📆 1 Месяц - {prices['1_month']} руб", False, "1_month"],
            [f"⏱ 6 Месяцев - {prices['6_months']} руб", False, "6_months"],
            [f"🔙 Назад", False, context.user_data.get("subscription_mode", "new_subscription")],
            [f"🏠 В главное меню", False, "main_menu"],
        ])
        text = (
            f"Сервер: {SERVERS_NAMES[context.user_data.get('server', DEFAULT)].capitalize()}\n"
            "Выберите период подписки:"
        )

    elif data in ["1_day", "1_week", "1_month", "6_months"]:
        context.user_data["subscription_type"] = data
        server = context.user_data.get("server", DEFAULT)
        price = await count_price(SUBSCRIPTION_PRICES[data], server)
        subscription_mode = context.user_data.get("subscription_mode", "new_subscription")
        mode_text = "Новая подписка" if subscription_mode == "new_subscription" else "Продление"
        attention = ""


        status = await xui.get_subscription_status(user_id)
        if mode_text == "Новая подписка" and status and server in status.keys():
            attention = "❕ ВНИМАНИЕ: Tы выбрал новую подписку на сервер, на котором она уже куплена.\nЕсли продолжишь, то АКТИВНАЯ подписка ПРОДЛИТСЯ на выбранный тобой срок\n\n"
        if mode_text == "Продление" and (not status or server not in status.keys()):
            attention = "❕ ВНИМАНИЕ: Tы выбрал продление подписки на сервер, на котором она еще не оформлена.\nЕсли продолжишь, то ОФОРМИТСЯ НОВАЯ подписка на выбранный тобой срок\n\n"
        text = (
            f"Ты выбрал:\n"
            f"🌐 Сервер: {SERVERS_NAMES[server].capitalize()}\n"
            f"🕒 Период: {TIME[data]}\n"
            f"💰 Цена: {price} RUB\n"
            f"📝 Тип: {mode_text}\n\n"
            f"{attention}"
            "Всё верно? 🤔"
        )
        reply_markup = create_keyboard([
            ["✅ Да", False, "confirm_payment"],
            ["❌ Нет", False, f"server-{server}"],
        ])

    elif data == "confirm_payment":
        data = context.user_data.get("subscription_type", "1_day")
        price = await count_price(SUBSCRIPTION_PRICES[data], context.user_data.get("server", DEFAULT))

        email = context.user_data.get("email")
        if not email:
            await query.edit_message_text("❌ Email не найден. Введите команду /set_email и попробуйте снова.")
            return

        payment = yooKassaClient.create_payment(
            amount=price,
            subscription_type=data,
            user_id=user_id,
            server=context.user_data.get("server", DEFAULT),
            chat_id=context._chat_id,
            message_id=query.message.message_id,
            user_email=email
        )

        payment_cryptomus_url = await cryptocloudClient.create_cryptocloud_payment(
            price=price,
            subscription_type=data,
            user_id=user_id,
            server=context.user_data.get("server", DEFAULT),
            chat_id=context._chat_id,
            message_id=query.message.message_id
        )

        reply_markup = create_keyboard([
            ["💳 Оплатить", True, payment.confirmation_url],
            ["💳 Оплатить криптовалютой", True, payment_cryptomus_url] if payment_cryptomus_url else ["💳 Оплатить криптовалютой (Недоступно)", False, "coming_soon"],
            ["🏠 В главное меню", False, "main_menu"],
        ])
        text=(f"Для оплаты {price} RUB нажмите кнопку 'Оплатить'\n\n"
            f"P.S. бот автоматически проверит статус оплаты и вышлет конфигурацию для подключения")

    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)


if __name__ == "__main__":
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("set_email", ask_email)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_email)],
        },
        fallbacks=[CallbackQueryHandler(button_handler, pattern="main_menu")],
    )
    app = ApplicationBuilder().token(TG_BOT_TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CallbackQueryHandler(button_handler))
    app.run_polling()
