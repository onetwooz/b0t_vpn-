# Работа с Telegram Payments

class TelegramPaymentsService:
    def __init__(self, provider_token):
        self.provider_token = provider_token

    def create_invoice(self, amount, description, user_id):
        # Создание счета через Telegram Payments
        pass

    def log_payment(self, user_id, amount, currency, status, details):
        from models.payment import Payment
        from database import SessionLocal
        session = SessionLocal()
        payment = Payment(
            user_id=user_id,
            amount=amount,
            currency=currency,
            provider='telegram',
            status=status,
            details=details,
        )
        session.add(payment)
        session.commit()
        session.close() 