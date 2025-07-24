# Сервис для отправки уведомлений пользователям

class NotificationService:
    def __init__(self, db, bot):
        self.db = db
        self.bot = bot

    async def notify_expiring_keys(self):
        from models.key import Key
        from models.user import User
        from datetime import datetime, timedelta
        now = datetime.utcnow()
        for days_left in [10, 1]:
            target_date = now + timedelta(days=days_left)
            keys = self.db.query(Key).filter(
                Key.expires_at >= target_date,
                Key.expires_at < target_date + timedelta(days=1),
                Key.used == True
            ).all()
            for key in keys:
                user = self.db.query(User).filter_by(id=key.issued_to).first()
                if user:
                    try:
                        await self.bot.send_message(
                            user.telegram_id,
                            f'Напоминание: срок действия вашего VPN-ключа для сервера {key.server.value} истекает через {days_left} день(дней).'
                        )
                    except Exception:
                        pass 