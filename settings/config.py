from datetime import timedelta
import os
from functools import lru_cache
from dotenv import load_dotenv

@lru_cache()
def load_env():
    load_dotenv()

def get_env_var(key: str, default=None):
    load_env()
    return os.getenv(key, default)

TG_BOT_TOKEN = get_env_var("TG_BOT_TOKEN")
YOOKASSA_SHOP_ID = get_env_var("YOOKASSA_SHOP_ID")
YOOKASSA_SECRET_KEY = get_env_var("YOOKASSA_SECRET_KEY")
CRYPTOCLOUD_API_KEY = get_env_var("CRYPTOCLOUD_API_KEY")
CRYPTOCLOUD_SHOP_ID = get_env_var("CRYPTOCLOUD_SHOP_ID")

SUPPORT_LINK = "https://organization-170.gitbook.io/reality-vpn"
MAX_CLIENTS = 80

SUBSCRIPTION_PRICES = {
    '1_day': {min: 10, max: 20},
    '1_week': {min: 40, max: 70},
    '1_month': {min: 90, max: 130},
    '6_months': {min: 480, max: 550}
}

SUBSCRIPTION_DURATION = {
    '1_day': timedelta(days=1),
    '1_week': timedelta(weeks=1),
    '1_month': timedelta(days=30),
    '6_months': timedelta(days=180)
}

TIME = {
    '1_day': "1 день",
    '1_week': "1 неделя",
    '1_month': "1 месяц",
    '6_months': "6 месяцев"
}

SERVERS_NAMES = {
    "france_1": "франция",
    "germany_1": "германия",
}


ALLOWED_IPS = [
    "185.71.76.0/27",
    "185.71.77.0/27",
    "77.75.153.0/25",
    "77.75.156.11",
    "77.75.156.35",
    "77.75.154.128/25",
    "2a02:5180::/32"
]