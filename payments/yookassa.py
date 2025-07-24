# Работа с YooKassa API

class YooKassaService:
    def __init__(self, shop_id, secret_key):
        self.shop_id = shop_id
        self.secret_key = secret_key

    def create_payment(self, amount, description, user_id, return_url=None):
        import requests
        import uuid
        url = 'https://api.yookassa.ru/v3/payments'
        headers = {
            'Content-Type': 'application/json',
            'Idempotence-Key': str(uuid.uuid4()),
        }
        auth = (self.shop_id, self.secret_key)
        data = {
            'amount': {
                'value': f'{amount:.2f}',
                'currency': 'RUB',
            },
            'confirmation': {
                'type': 'redirect',
                'return_url': return_url or 'https://t.me/your_bot',
            },
            'capture': True,
            'description': description,
            'metadata': {
                'user_id': user_id
            }
        }
        response = requests.post(url, json=data, headers=headers, auth=auth)
        if response.status_code == 200:
            resp = response.json()
            return resp['confirmation']['confirmation_url'], resp['id']
        return None, None

    def handle_webhook(self, data):
        # Обработка уведомления от YooKassa
        pass 