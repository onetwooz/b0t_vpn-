import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from handlers import user, admin
from scheduler import start_scheduler

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(user.router)
    dp.include_router(admin.router)
    start_scheduler(bot)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main()) 