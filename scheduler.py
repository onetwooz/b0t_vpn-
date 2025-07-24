from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.notification import NotificationService
from database import SessionLocal
import asyncio

scheduler = AsyncIOScheduler()

# Функция-обертка для запуска асинхронного метода из APScheduler
async def notify_job(bot):
    session = SessionLocal()
    service = NotificationService(session, bot)
    await service.notify_expiring_keys()
    session.close()

def start_scheduler(bot):
    scheduler.start()
    # Запускать уведомления каждый день в 10:00
    scheduler.add_job(lambda: asyncio.create_task(notify_job(bot)), 'cron', hour=10, minute=0) 