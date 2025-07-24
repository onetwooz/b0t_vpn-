from aiogram import Router, types
from aiogram.filters import Command
from config import ADMIN_ID
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(Command('adm_users'))
async def cmd_adm_users(message: types.Message):
    await message.answer('Админ-команда: информация по пользователям (в разработке).')

@router.message(Command('adm_load_keys'))
async def cmd_adm_load_keys(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text='Германия'))
    kb.add(types.KeyboardButton(text='США'))
    await message.answer('Выберите сервер для загрузки ключей:', reply_markup=kb)

    @router.message()
    async def process_server(msg: types.Message):
        country = msg.text.lower()
        if country == 'германия':
            server = 'germany'
        elif country == 'сша':
            server = 'usa'
        else:
            await msg.answer('Пожалуйста, выберите сервер из списка.')
            return
        await msg.answer('Пришлите ссылку на список ключей (один ключ в строке):', reply_markup=types.ReplyKeyboardRemove())

        @router.message()
        async def process_keys_url(msg2: types.Message):
            url = msg2.text.strip()
            from services.key_manager import KeyManager
            from database import SessionLocal
            session = SessionLocal()
            key_manager = KeyManager(session)
            count = key_manager.load_keys_from_url(url, server)
            await msg2.answer(f'Загружено {count} ключей для сервера {server}.')

@router.message(Command('adm_del_key'))
async def cmd_adm_del_key(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    await message.answer('Пришлите ключ, который нужно удалить:')

    @router.message()
    async def process_del_key(msg: types.Message):
        key_str = msg.text.strip()
        await msg.answer(f'Вы уверены, что хотите удалить ключ {key_str}? (да/нет)')

        @router.message()
        async def confirm_del_key(msg2: types.Message):
            if msg2.text.lower() == 'да':
                from services.key_manager import KeyManager
                from database import SessionLocal
                session = SessionLocal()
                key_manager = KeyManager(session)
                deleted = key_manager.delete_key(key_str)
                if deleted:
                    await msg2.answer('Ключ удалён.')
                else:
                    await msg2.answer('Ключ не найден.')
            else:
                await msg2.answer('Удаление отменено.')

@router.message(Command('adm_user'))
async def cmd_adm_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    await message.answer('Пришлите Telegram ID пользователя:')

    @router.message()
    async def process_user_id(msg: types.Message):
        user_id = msg.text.strip()
        from database import SessionLocal
        from models.user import User
        session = SessionLocal()
        user = session.query(User).filter_by(telegram_id=user_id).first()
        if not user:
            await msg.answer('Пользователь не найден.')
            return
        text = f'ID: {user.telegram_id}\nUsername: @{user.username}\nИмя: {user.full_name}\nЗарегистрирован: {user.registered_at.strftime("%d.%m.%Y %H:%M")}'
        await msg.answer(text)

@router.message(Command('adm_user_keys'))
async def cmd_adm_user_keys(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    await message.answer('Пришлите Telegram ID пользователя:')

    @router.message()
    async def process_user_id_keys(msg: types.Message):
        user_id = msg.text.strip()
        from database import SessionLocal
        from models.key import Key
        session = SessionLocal()
        keys = session.query(Key).filter_by(issued_to=user_id).all()
        if not keys:
            await msg.answer('У пользователя нет выданных ключей.')
            return
        text = f'Ключи пользователя {user_id}:\n'
        for key in keys:
            text += f'Ключ: {key.key}\nСервер: {key.server.value}\nВыдан: {key.issued_at}\nДействует до: {key.expires_at}\n---\n'
        await msg.answer(text)

@router.message(Command('adm_payments'))
async def cmd_adm_payments(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    from database import SessionLocal
    from models.payment import Payment
    session = SessionLocal()
    payments = session.query(Payment).order_by(Payment.created_at.desc()).limit(10).all()
    if not payments:
        await message.answer('Платежей нет.')
        return
    text = 'Последние платежи:\n'
    for p in payments:
        text += f'UserID: {p.user_id}, {p.amount} {p.currency}, {p.provider}, {p.status}, {p.created_at.strftime("%d.%m.%Y %H:%M")}\n'
    await message.answer(text)

@router.message(Command('adm_payments_user'))
async def cmd_adm_payments_user(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    await message.answer('Пришлите Telegram ID пользователя:')
    @router.message()
    async def process_user_id(msg: types.Message):
        user_id = msg.text.strip()
        from database import SessionLocal
        from models.payment import Payment
        session = SessionLocal()
        payments = session.query(Payment).filter_by(user_id=user_id).order_by(Payment.created_at.desc()).all()
        if not payments:
            await msg.answer('Платежей нет.')
            return
        text = f'Платежи пользователя {user_id}:\n'
        for p in payments:
            text += f'{p.amount} {p.currency}, {p.provider}, {p.status}, {p.created_at}\n'
        await msg.answer(text)

@router.message(Command('adm_export_payments'))
async def cmd_adm_export_payments(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    from database import SessionLocal
    from models.payment import Payment
    import csv, io
    session = SessionLocal()
    payments = session.query(Payment).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['user_id', 'amount', 'currency', 'provider', 'status', 'created_at'])
    for p in payments:
        writer.writerow([p.user_id, p.amount, p.currency, p.provider, p.status, p.created_at])
    output.seek(0)
    await message.answer_document(types.BufferedInputFile(output.getvalue().encode('utf-8'), filename='payments.csv'))

@router.message(Command('adm_export_users'))
async def cmd_adm_export_users(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    from database import SessionLocal
    from models.user import User
    import csv, io
    session = SessionLocal()
    users = session.query(User).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['telegram_id', 'username', 'full_name', 'registered_at'])
    for u in users:
        writer.writerow([u.telegram_id, u.username, u.full_name, u.registered_at])
    output.seek(0)
    await message.answer_document(types.BufferedInputFile(output.getvalue().encode('utf-8'), filename='users.csv'))

@router.message(Command('adm_export_keys'))
async def cmd_adm_export_keys(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    from database import SessionLocal
    from models.key import Key
    import csv, io
    session = SessionLocal()
    keys = session.query(Key).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['key', 'server', 'is_trial', 'issued_to', 'issued_at', 'expires_at', 'used'])
    for k in keys:
        writer.writerow([k.key, k.server.value, k.is_trial, k.issued_to, k.issued_at, k.expires_at, k.used])
    output.seek(0)
    await message.answer_document(types.BufferedInputFile(output.getvalue().encode('utf-8'), filename='keys.csv'))

@router.message(Command('adm_keys_server'))
async def cmd_adm_keys_server(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(types.KeyboardButton(text='Германия'))
    kb.add(types.KeyboardButton(text='США'))
    await message.answer('Выберите сервер:', reply_markup=kb)
    @router.message()
    async def process_server(msg: types.Message):
        country = msg.text.lower()
        if country == 'германия':
            server = 'germany'
        elif country == 'сша':
            server = 'usa'
        else:
            await msg.answer('Пожалуйста, выберите сервер из списка.')
            return
        from database import SessionLocal
        from models.key import Key, ServerLocation
        session = SessionLocal()
        keys = session.query(Key).filter_by(server=ServerLocation(server)).all()
        if not keys:
            await msg.answer('Ключей для этого сервера нет.', reply_markup=types.ReplyKeyboardRemove())
            return
        text = f'Ключи сервера {country.capitalize()}:\n'
        for k in keys:
            text += f'{k.key} | trial: {k.is_trial} | выдан: {k.issued_to} | до: {k.expires_at}\n'
        await msg.answer(text, reply_markup=types.ReplyKeyboardRemove()) 

@router.message(Command('adm_users_period'))
async def cmd_adm_users_period(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    await message.answer('Пришлите даты в формате ДД.ММ.ГГГГ-ДД.ММ.ГГГГ (например, 01.01.2024-31.01.2024):')
    @router.message()
    async def process_period(msg: types.Message):
        import datetime
        try:
            date_from_str, date_to_str = msg.text.strip().split('-')
            date_from = datetime.datetime.strptime(date_from_str.strip(), '%d.%m.%Y')
            date_to = datetime.datetime.strptime(date_to_str.strip(), '%d.%m.%Y')
        except Exception:
            await msg.answer('Неверный формат дат. Пример: 01.01.2024-31.01.2024')
            return
        from database import SessionLocal
        from models.user import User
        session = SessionLocal()
        users = session.query(User).filter(User.registered_at >= date_from, User.registered_at <= date_to).all()
        if not users:
            await msg.answer('Пользователей за этот период нет.')
            return
        text = f'Пользователи с {date_from_str} по {date_to_str}:\n'
        for u in users:
            text += f'{u.telegram_id} | @{u.username} | {u.full_name} | {u.registered_at}\n'
        await msg.answer(text) 

@router.message(Command('adm_stats'))
async def cmd_adm_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    from database import SessionLocal
    from models.user import User
    from models.payment import Payment
    from models.key import Key
    session = SessionLocal()
    users_count = session.query(User).count()
    payments_count = session.query(Payment).count()
    keys_count = session.query(Key).count()
    text = (
        f'Пользователей: {users_count}\n'
        f'Платежей: {payments_count}\n'
        f'Ключей в базе: {keys_count}'
    )
    await message.answer(text) 

@router.message(Command('adm_maintenance_on'))
async def cmd_maintenance_on(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    with open('maintenance_mode.flag', 'w') as f:
        f.write('on')
    await message.answer('Режим обслуживания ВКЛЮЧЕН. Пользователи не смогут совершать покупки.')

@router.message(Command('adm_maintenance_off'))
async def cmd_maintenance_off(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    import os
    if os.path.exists('maintenance_mode.flag'):
        os.remove('maintenance_mode.flag')
    await message.answer('Режим обслуживания ВЫКЛЮЧЕН. Покупки снова доступны.') 

@router.message(Command('admin'))
async def cmd_admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer('Доступ запрещён.')
        return
    kb = InlineKeyboardBuilder()
    kb.button(text="Пользователи", callback_data="adm_users")
    kb.button(text="Ключи", callback_data="adm_keys")
    kb.button(text="Платежи", callback_data="adm_payments")
    kb.button(text="Экспорт", callback_data="adm_export")
    kb.button(text="Статистика", callback_data="adm_stats")
    kb.button(text="Обслуживание", callback_data="adm_maintenance")
    kb.adjust(2)
    await message.answer(
        'Админ-панель. Выберите действие:',
        reply_markup=kb.as_markup()
    )

@router.callback_query(lambda c: c.data == "adm_users")
async def cb_adm_users(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_adm_users(callback.message)
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_keys")
async def cb_adm_keys(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_adm_keys_server(callback.message) # Assuming cmd_adm_keys is a placeholder for cmd_adm_keys_server
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_payments")
async def cb_adm_payments(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_adm_payments(callback.message)
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_export")
async def cb_adm_export(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="Экспорт пользователей", callback_data="adm_export_users")
    kb.button(text="Экспорт ключей", callback_data="adm_export_keys")
    kb.button(text="Экспорт платежей", callback_data="adm_export_payments")
    kb.adjust(1)
    await callback.message.edit_text('Выберите экспорт:', reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_export_users")
async def cb_adm_export_users(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_adm_export_users(callback.message)
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_export_keys")
async def cb_adm_export_keys(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_adm_export_keys(callback.message)
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_export_payments")
async def cb_adm_export_payments(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_adm_export_payments(callback.message)
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_stats")
async def cb_adm_stats(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_adm_stats(callback.message)
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_maintenance")
async def cb_adm_maintenance(callback: types.CallbackQuery):
    kb = InlineKeyboardBuilder()
    kb.button(text="Включить обслуживание", callback_data="adm_maintenance_on")
    kb.button(text="Выключить обслуживание", callback_data="adm_maintenance_off")
    kb.adjust(1)
    await callback.message.edit_text('Режим обслуживания:', reply_markup=kb.as_markup())
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_maintenance_on")
async def cb_adm_maintenance_on(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_maintenance_on(callback.message)
    await callback.answer()

@router.callback_query(lambda c: c.data == "adm_maintenance_off")
async def cb_adm_maintenance_off(callback: types.CallbackQuery):
    await callback.message.delete_reply_markup()
    await cmd_maintenance_off(callback.message)
    await callback.answer() 