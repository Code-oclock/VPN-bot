import logging
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

SUPPORT_CHAT_ID = -4682106238

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Команда /start. Информирует пользователя, как создать запрос.
    """
    await update.message.reply_text(
        "👋 Привет!\nЧтобы создать запрос в службу поддержки, просто напишите ваше сообщение.\n"
    )


async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает сообщения пользователей в приватном чате.
    Сообщение копируется в чат поддержки, а соответствие (mapping) сохраняется.
    """
    if update.effective_chat.type != "private":
        return

    try:
        await context.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=f"✍️ New message from user: {update.effective_user.id}")

        forwarded_message = await context.bot.forward_message(
            chat_id=SUPPORT_CHAT_ID,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )

        context.bot_data[str(forwarded_message.message_id)] = update.effective_user.id

        await update.message.reply_text("✅ Ваш запрос отправлен в службу поддержки. Ожидайте ответа.")

    except Exception as e:
        await context.bot.send_message(
            chat_id=SUPPORT_CHAT_ID,
            text=f"Произошла ошибка у пользователя: {e.__str__()}")
        await update.message.reply_text("Произошла ошибка при отправке запроса. Попробуйте позже.")


async def handle_manager_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обрабатывает сообщения в чате поддержки.
    Если сообщение является ответом (reply) на запрос пользователя, бот копирует ответ пользователю.
    """

    if update.effective_chat.id != SUPPORT_CHAT_ID:
        return

    if not update.message.reply_to_message:
        return

    user_chat_id = context.bot_data.get(str(update.message.reply_to_message.message_id))
    context.bot_data.pop(str(update.message.reply_to_message.message_id))

    try:

        # msg = await update.effective_message.copy(chat_id=user_chat_id)

        await context.bot.send_message(
            chat_id=user_chat_id,
            text=f"Ответ службы поддержки: {update.effective_message.text}"
        )
        await update.message.reply_text("Ответ отправлен пользователю.")

    except Exception as e:
        await update.message.reply_text("Произошла ошибка при отправке ответа пользователю:", e.__str__())


if __name__ == '__main__':
    BOT_TOKEN = "8093044579:AAHgDMZ2sAHHNwg9KbptdqsPYyJQ2RHPX_k"

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, handle_user_message))
    app.add_handler(MessageHandler(filters.Chat(SUPPORT_CHAT_ID) & filters.REPLY, handle_manager_reply))

    logger.info("Бот запущен...")
    app.run_polling()