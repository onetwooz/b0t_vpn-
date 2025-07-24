import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY')
YOOKASSA_WEBHOOK_URL = os.getenv('YOOKASSA_WEBHOOK_URL')
TELEGRAM_PAYMENTS_TOKEN = os.getenv('TELEGRAM_PAYMENTS_TOKEN')
DB_URL = os.getenv('DB_URL', 'sqlite:///vpn_bot.db') 