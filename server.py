import logging
from telegram.ext import Application, MessageHandler, filters, CommandHandler, ConversationHandler
from telegram import ReplyKeyboardMarkup, Bot, ReplyKeyboardRemove
from config import BOT_TOKEN
import json
import aiohttp
from flask import jsonify


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG
)

logger = logging.getLogger(__name__)
bot = Bot(BOT_TOKEN)


async def load_json(update, context):
    file_info = await bot.get_file(update.message.document.file_id)
    file = await file_info.download_as_bytearray()
    context.user_data['QUESTIONS'] = json.loads(file)['test']
    await update.message.reply_text('Файл загружен.')


async def start(update, context):
    if not context.user_data.get('QUESTIONS'):
        await update.message.reply_text('Вы не загрузили файл для тестирования!')
        return ConversationHandler.END
    context.user_data['score'] = 0
    context.user_data['limit'] = len(context.user_data['QUESTIONS'])
    context.user_data['curr'] = 0
    await update.message.reply_text(f"Привет. Начинаем викторину!\nСчет: 0"
                                    f"/{context.user_data['limit']}")
    await update.message.reply_text(f"Вопрос №{context.user_data['curr'] + 1}.")
    await update.message.reply_text(context.user_data['QUESTIONS'][context.user_data['curr']]
                                    ['question'])
    return 1


async def get_ans(update, context):
    ans = update.message.text
    if ans != context.user_data['QUESTIONS'][context.user_data['curr']]['response']:
        await update.message.reply_text('Неверный ответ. Идем дальше.')
    else:
        await update.message.reply_text('Верный ответ. Идем дальше.')
        context.user_data['score'] += 1
    context.user_data['curr'] += 1
    if context.user_data['curr'] < context.user_data['limit']:
        await update.message.reply_text(f"Счет: {context.user_data['score']}"
                                        f"/{context.user_data['limit']}")
        await update.message.reply_text(f"Вопрос №{context.user_data['curr'] + 1}.")
        await update.message.reply_text(context.user_data['QUESTIONS'][context.user_data['curr']]
                                        ['question'])
        return 1
    else:
        await update.message.reply_text('Викторина завершена!')
        await update.message.reply_text(f"Счет: {context.user_data['score']}"
                                        f"/{context.user_data['limit']}")
        context.user_data['score'] = 0
        context.user_data['limit'] = 0
        context.user_data['curr'] = 0
        return ConversationHandler.END


async def stop(update, context):
    context.user_data['score'] = 0
    context.user_data['limit'] = 0
    context.user_data['curr'] = 0
    await update.message.reply_text("Тестирование оборвано. Прогресс обнулен.")
    return ConversationHandler.END


def main():
    application = Application.builder().token(BOT_TOKEN).build()

    load_json_handler = MessageHandler(filters.Document.FileExtension('json'), load_json)
    application.add_handler(load_json_handler)
    testirovanie = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ans)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )
    application.add_handler(testirovanie)
    application.run_polling()


if __name__ == '__main__':
    main()
