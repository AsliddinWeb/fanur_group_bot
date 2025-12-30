import os
from dotenv import load_dotenv

load_dotenv()

# Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_NAME = os.getenv("BOT_NAME", "Fanur Group Bot")

# Owner (asosiy admin)
OWNER_ID = int(os.getenv("OWNER_ID"))

# Kanal
CHANNEL_ID = os.getenv("CHANNEL_ID")
CHANNEL_URL = os.getenv("CHANNEL_URL")

# Yopiq kanal (to'lov qilganlar uchun)
PRIVATE_CHANNEL_URL = os.getenv("PRIVATE_CHANNEL_URL")
PRIVATE_CHANNEL_ID = int(os.getenv("PRIVATE_CHANNEL_ID"))

# Admin username (yordam uchun)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")

# To'lov summasi
PAYMENT_AMOUNT = int(os.getenv("PAYMENT_AMOUNT", 97000))  # so'm

# Database
DB_PATH = os.getenv("DB_PATH", "bot.db")

# Payme
PAYME_MERCHANT_ID = os.getenv("PAYME_MERCHANT_ID")
PAYME_SECRET_KEY = os.getenv("PAYME_SECRET_KEY")
PAYME_TEST_KEY = os.getenv("PAYME_TEST_KEY")
PAYME_AMOUNT = int(os.getenv("PAYME_AMOUNT", 9700000))  # tiyin
PAYME_TEST_MODE = os.getenv("PAYME_TEST_MODE", "false").lower() == "true"
PAYME_CHECKOUT_URL = os.getenv("PAYME_CHECKOUT_URL", "https://checkout.paycom.uz")
PAYME_TEST_CHECKOUT_URL = os.getenv("PAYME_TEST_CHECKOUT_URL", "https://test.paycom.uz")

# Broadcast
BROADCAST_DELAY = float(os.getenv("BROADCAST_DELAY", 0.05))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")