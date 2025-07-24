from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from payments.telegram_pay import TelegramPaymentsService
from services.key_manager import KeyManager
from database import SessionLocal
from models.key import ServerLocation
from aiogram.filters import CommandObject
from utils.helpers import log_error
from config import ADMIN_ID
import os
from aiogram import Bot

router = Router()

@router.message(Command('start'))
async def cmd_start(message: types.Message):
    await message.answer('Добро пожаловать! Это бот для покупки VPN-ключей.')

@router.message(Command('profile'))
async def cmd_profile(message: types.Message):
    # Здесь будет логика получения профиля пользователя
    await message.answer(f'Ваш Telegram ID: {message.from_user.id}')

@router.message(Command('cancel'))
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer('Действие отменено.', reply_markup=types.ReplyKeyboardRemove())

@router.message(Command('trial'))
async def cmd_trial(message: types.Message):
    from services.user_manager import UserManager
    from services.key_manager import KeyManager
    from database import SessionLocal
    from models.key import ServerLocation
    session = SessionLocal()
    user_manager = UserManager(session)
    key_manager = KeyManager(session)
    user = user_manager.get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        full_name=message.from_user.full_name or ''
    )
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text='Германия'))
    kb.add(types.KeyboardButton(text='США'))
    await message.answer('Выберите сервер для пробного ключа (или /cancel для отмены):', reply_markup=kb)

    @router.message()
    async def process_trial_country(msg: types.Message):
        if msg.text.lower() == '/cancel':
            await cancel_handler(msg, state=None)
            return
        country = msg.text.lower()
        if country == 'германия':
            server = ServerLocation.germany
        elif country == 'сша':
            server = ServerLocation.usa
        else:
            await msg.answer('Пожалуйста, выберите сервер из списка или /cancel для отмены.')
            return

        # Проверка лимита на пробный ключ
        if key_manager.has_recent_trial(user.id, server):
            await msg.answer('Вы уже получали пробный ключ для этого сервера в этом месяце.', reply_markup=types.ReplyKeyboardRemove())
            return

        try:
            key = key_manager.issue_key(user.id, server, period=3, is_trial=True)
            if key:
                await msg.answer(f'Ваш пробный ключ: {key.key}\nСрок действия: 3 дня', reply_markup=types.ReplyKeyboardRemove())
            else:
                await msg.answer('Пробные ключи для этого сервера закончились.', reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            await msg.answer(f'Произошла ошибка: {e}\nПопробуйте еще раз или обратитесь в поддержку.', reply_markup=types.ReplyKeyboardRemove())
            await log_error(f'FSM /trial: {e}')

class BuyStates(StatesGroup):
    choosing_country = State()
    choosing_period = State()
    confirming_payment = State()

@router.message(Command('buy'))
async def cmd_buy(message: types.Message, state: FSMContext):
    if os.path.exists('maintenance_mode.flag'):
        await message.answer('В данный момент ведутся технические работы. Покупки временно недоступны.')
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text='Германия'))
    kb.add(types.KeyboardButton(text='США'))
    await message.answer('Выберите сервер для покупки ключа (или /cancel для отмены):', reply_markup=kb)
    await state.set_state(BuyStates.choosing_country)

@router.message(BuyStates.choosing_country)
async def buy_choose_country(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await cancel_handler(message, state)
        return
    country = message.text.lower()
    if country == 'германия':
        server = 'germany'
    elif country == 'сша':
        server = 'usa'
    else:
        await message.answer('Пожалуйста, выберите сервер из списка или /cancel для отмены.')
        return
    await state.update_data(server=server)
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text='1 месяц'))
    kb.add(types.KeyboardButton(text='3 месяца'))
    kb.add(types.KeyboardButton(text='6 месяцев'))
    kb.add(types.KeyboardButton(text='12 месяцев'))
    await message.answer('Выберите срок действия ключа (или /cancel для отмены):', reply_markup=kb)
    await state.set_state(BuyStates.choosing_period)

@router.message(BuyStates.choosing_period)
async def buy_choose_period(message: types.Message, state: FSMContext):
    if message.text.lower() == '/cancel':
        await cancel_handler(message, state)
        return
    period_map = {
        '1 месяц': 1,
        '3 месяца': 3,
        '6 месяцев': 6,
        '12 месяцев': 12
    }
    period = period_map.get(message.text)
    if not period:
        await message.answer('Пожалуйста, выберите срок из списка или /cancel для отмены.')
        return
    await state.update_data(period=period)
    data = await state.get_data()
    # Здесь можно рассчитать цену
    price = 100 * period  # Пример: 100 руб/мес
    await message.answer(f'Стоимость ключа: {price} руб.\nВыберите способ оплаты (или /cancel для отмены):', reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add('YooKassa').add('Telegram'))
    await state.set_state(BuyStates.confirming_payment)

@router.message(BuyStates.confirming_payment)
async def buy_confirm_payment(message: types.Message, state: FSMContext):
    if os.path.exists('maintenance_mode.flag'):
        await message.answer('В данный момент ведутся технические работы. Покупки временно недоступны.', reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return
    if message.text.lower() == '/cancel':
        await cancel_handler(message, state)
        return
    try:
        pay_method = message.text.lower()
        data = await state.get_data()
        period = data.get('period')
        server = data.get('server')
        price = 100 * period
        if pay_method == 'yookassa':
            from payments.yookassa import YooKassaService
            from config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
            service = YooKassaService(YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY)
            description = f'VPN ключ: {server}, {period} мес.'
            confirmation_url, payment_id = service.create_payment(
                amount=price,
                description=description,
                user_id=message.from_user.id,
                return_url='https://t.me/your_bot'
            )
            if confirmation_url:
                await message.answer(f'Перейдите по ссылке для оплаты:\n{confirmation_url}\nПосле оплаты ключ будет выдан автоматически.', reply_markup=types.ReplyKeyboardRemove())
            else:
                await message.answer('Ошибка при создании платежа через YooKassa. Попробуйте позже или обратитесь в поддержку.', reply_markup=types.ReplyKeyboardRemove())
                await log_error(f'Ошибка создания платежа YooKassa для user_id={message.from_user.id}, server={server}, period={period}')
        elif pay_method == 'telegram':
            from config import TELEGRAM_PAYMENTS_TOKEN
            title = f'VPN ключ {server.upper()} ({period} мес.)'
            description = f'VPN ключ для сервера {server.upper()} на {period} мес.'
            payload = f'{message.from_user.id}:{server}:{period}'
            prices = [types.LabeledPrice(label=title, amount=price*100)]
            await message.bot.send_invoice(
                chat_id=message.chat.id,
                title=title,
                description=description,
                payload=payload,
                provider_token=TELEGRAM_PAYMENTS_TOKEN,
                currency='RUB',
                prices=prices,
                start_parameter='vpn-buy',
                need_email=False
            )
            await message.answer('Счет через Telegram Payments отправлен. После оплаты ключ будет выдан автоматически.', reply_markup=types.ReplyKeyboardRemove())
        else:
            await message.answer('Пожалуйста, выберите способ оплаты из списка или /cancel для отмены.')
            return
    except Exception as e:
        await message.answer(f'Произошла ошибка: {e}\nПопробуйте еще раз или обратитесь в поддержку.', reply_markup=types.ReplyKeyboardRemove())
        await log_error(f'FSM /buy: {e}')
    await state.clear()

@router.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery, bot: Bot):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@router.message()
async def process_successful_payment(message: types.Message):
    if not message.successful_payment:
        return
    payload = message.successful_payment.invoice_payload
    try:
        user_id, server, period = payload.split(':')
        period = int(period)
    except Exception as e:
        await message.answer('Ошибка при обработке платежа. Обратитесь в поддержку.')
        await log_error(f'Ошибка парсинга payload Telegram Payments: {e}')
        return
    session = SessionLocal()
    key_manager = KeyManager(session)
    try:
        key = key_manager.issue_key(user_id, ServerLocation(server), period, is_trial=False)
        if key:
            await message.answer(f'Спасибо за оплату! Ваш ключ: {key.key}\nСервер: {server}\nСрок действия: {period} мес.')
            await message.bot.send_message(ADMIN_ID, f'Новый платёж (Telegram): user_id={user_id}, сервер={server}, период={period}, сумма={message.successful_payment.total_amount/100} {message.successful_payment.currency}')
        else:
            await message.answer(f'Спасибо за оплату! К сожалению, ключи для сервера {server} закончились. Свяжитесь с поддержкой.')
            await message.bot.send_message(ADMIN_ID, f'ВНИМАНИЕ: Ключи для сервера {server} закончились! user_id={user_id}, период={period}')
    except Exception as e:
        await message.answer('Ошибка при выдаче ключа. Обратитесь в поддержку.')
        await log_error(f'Ошибка выдачи ключа Telegram Payments: {e}')
    from payments.telegram_pay import TelegramPaymentsService
    service = TelegramPaymentsService(provider_token=None)
    try:
        service.log_payment(
            user_id=user_id,
            amount=message.successful_payment.total_amount / 100,
            currency=message.successful_payment.currency,
            status='succeeded',
            details=str(message.successful_payment)
        )
    except Exception as e:
        await log_error(f'Ошибка логирования платежа Telegram Payments: {e}')
    session.close()

@router.message(Command('mykeys'))
async def cmd_mykeys(message: types.Message):
    from database import SessionLocal
    from models.key import Key, ServerLocation
    session = SessionLocal()
    keys = session.query(Key).filter(
        Key.issued_to == message.from_user.id,
        Key.expires_at > Key.issued_at  # ключ активен
    ).all()
    if not keys:
        await message.answer('У вас нет активных ключей.')
        return
    text = 'Ваши активные ключи:\n'
    for key in keys:
        text += f'\nКлюч: {key.key}\nСервер: {key.server.value}\nДействует до: {key.expires_at.strftime("%d.%m.%Y %H:%M")}\n'
    await message.answer(text)

@router.message(Command('help'))
async def cmd_help(message: types.Message):
    text = (
        'Доступные команды:\n'
        '/buy — купить VPN-ключ\n'
        '/trial — получить пробный ключ\n'
        '/mykeys — посмотреть свои ключи\n'
        '/profile — профиль\n'
        '/cancel — отменить действие\n'
        '/help — справка\n'
        '/support — связаться с поддержкой'
    )
    await message.answer(text)

@router.message(Command('support'))
async def cmd_support(message: types.Message):
    await message.answer('По вопросам поддержки пишите: @your_support_username или на email support@example.com') 