from fastapi import FastAPI, Request
from aiogram import Bot
from config import BOT_TOKEN
from database import SessionLocal
from services.key_manager import KeyManager
from models.key import ServerLocation
from models.payment import Payment
from utils.helpers import log_error

app = FastAPI()

bot = Bot(token=BOT_TOKEN)

@app.post('/api/yookassa/webhook')
async def yookassa_webhook(request: Request):
    data = await request.json()
    # Проверяем статус платежа
    if data.get('object', {}).get('status') == 'succeeded':
        metadata = data['object'].get('metadata', {})
        user_id = metadata.get('user_id')
        description = data['object'].get('description', '')
        # Парсим сервер и период из description
        # Ожидается формат: 'VPN ключ: germany, 3 мес.'
        try:
            parts = description.split(':')[1].strip().split(',')
            server = parts[0].strip()
            period = int(parts[1].replace('мес.', '').strip())
        except Exception:
            server = 'germany'
            period = 1
        session = SessionLocal()
        key_manager = KeyManager(session)
        key = key_manager.issue_key(user_id, ServerLocation(server), period, is_trial=False)
        if key:
            await bot.send_message(int(user_id), f'Спасибо за оплату! Ваш ключ: {key.key}\nСервер: {server}\nСрок действия: {period} мес.')
            await bot.send_message(ADMIN_ID, f'Новый платёж: user_id={user_id}, сервер={server}, период={period}, сумма={data["object"]["amount"]["value"]} {data["object"]["amount"]["currency"]}')
        else:
            await bot.send_message(int(user_id), f'Спасибо за оплату! К сожалению, ключи для сервера {server} закончились. Свяжитесь с поддержкой.')
            await bot.send_message(ADMIN_ID, f'ВНИМАНИЕ: Ключи для сервера {server} закончились! user_id={user_id}, период={period}')
        # Логируем платеж
        payment = Payment(
            user_id=user_id,
            amount=data['object']['amount']['value'],
            currency=data['object']['amount']['currency'],
            provider='yookassa',
            status=data['object']['status'],
            details=str(data['object']),
        )
        session.add(payment)
        session.commit()
        session.close()
    return {'status': 'ok'}

@app.get('/api/health')
async def healthcheck():
    return {'status': 'ok'} 