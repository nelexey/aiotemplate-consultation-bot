from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str

    DB_USER: str
    DB_PASS: str
    DB_HOST: str
    DB_PORT: int
    DB_NAME: str

    WEB_HOST: str
    WEB_PORT: int
    WEB_TIMEOUT: int = 60
    WEB_MAX_CONNECTIONS: int = 100

    WEB_SERVICE_HOST: str
    WEB_SERVICE_PORT: int

    WEB_WEBHOOK_PATH: str

    ADMIN_IDS: str  # ID администраторов через запятую

    BOOKING_LIMIT: int = 3  # Максимальное количество активных бронирований на пользователя

    CURRENCY: str = "RUB"  # Валюта по умолчанию
    CURRENCY_SYMBOL: str = "₽"  # Символ валюты по умолчанию

    MAX_DEPOSIT_AMOUNT: float = 1000000  # Максимальная сумма пополнения баланса

    YOOKASSA_SHOP_ID: str
    YOOKASSA_SECRET_KEY: str
    YOOKASSA_RETURN_URL: str
    CONSULTATION_PRICE: float


    @property
    def database_url(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @property
    def bot_token(self) -> str:
        return self.BOT_TOKEN

    @property
    def web_config(self) -> dict:
        return {'host': self.WEB_HOST,
                'port': self.WEB_PORT,
                'timeout': self.WEB_TIMEOUT,
                'max_connections': self.WEB_MAX_CONNECTIONS,
                }

    @property
    def some_service_url(self) -> str:
        return f"http://{self.WEB_SERVICE_HOST}:{self.WEB_SERVICE_PORT}"

    @property
    def admin_id(self) -> int:
        """Returns first admin ID from the list"""
        return int(self.ADMIN_IDS.split(',')[0])

    @property
    def admin_ids(self) -> list[int]:
        """Returns list of all admin IDs"""
        return [int(admin_id.strip()) for admin_id in self.ADMIN_IDS.split(',')]
    
    def yookassa_config(self) -> dict:
        return {
            'shop_id': self.YOOKASSA_SHOP_ID,
            'secret_key': self.YOOKASSA_SECRET_KEY
        }
    
    def yookassa_payment_config(self) -> dict:
        return {
            'amount': {
                'value': self.CONSULTATION_PRICE,
                'currency': self.CURRENCY
            },
            'return_url': self.YOOKASSA_RETURN_URL,
            'confirmation_type': 'redirect',
            'confirmation_return_url': self.YOOKASSA_RETURN_URL
        }

    @property
    def currency_info(self) -> dict:
        return {
            'code': self.CURRENCY,
            'symbol': self.CURRENCY_SYMBOL
        }


settings = Settings(_env_file='.env')