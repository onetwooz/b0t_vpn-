# Вспомогательные функции для бота

import logging
from config import ADMIN_ID, BOT_TOKEN
from aiogram import Bot

logging.basicConfig(filename='bot_errors.log', level=logging.ERROR, format='%(asctime)s %(levelname)s %(message)s')

async def log_error(error_text):
    logging.error(error_text)
    # Отправка админу в Telegram (опционально)
    try:
        bot = Bot(token=BOT_TOKEN)
        await bot.send_message(ADMIN_ID, f'Ошибка: {error_text}')
    except Exception:
        pass

def format_key_info(key):
    # Форматирование информации о ключе для вывода пользователю
    pass 