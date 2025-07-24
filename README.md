<<<<<<< HEAD
# b0t_vpn-

Бот для продажи VPN-ключей с оплатой через YooKassa и Telegram Payments.

## Быстрый старт

1. Скопируйте `.env.example` в `.env` и заполните переменные.
2. Установите зависимости:
   ```
   pip install -r requirements.txt
   ```
3. Запустите бота:
   ```
   python bot.py
   ```

## Структура проекта
- `bot.py` — точка входа
- `config.py` — конфиг
- `database.py` — база данных
- `handlers/` — обработчики команд
- `models/` — ORM-модели
- `services/` — бизнес-логика
- `payments/` — интеграция с YooKassa и Telegram Payments
- `api/` — HTTP endpoint для уведомлений YooKassa
- `scheduler.py` — планировщик задач 
>>>>>>> dbb597a (Initial commit)
