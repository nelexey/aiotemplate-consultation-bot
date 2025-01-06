from yookassa import Payment, Configuration
import uuid
import asyncio
from bot.database.methods.create import create_payment as db_create_payment
from bot.misc.env import settings
from bot.services.payment_handler import handle_payment_status

class YookassaService:
    _instance = None
    _bot = None

    def __new__(cls, shop_id: str = None, secret_key: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.shop_id = shop_id
            cls._instance.secret_key = secret_key
            Configuration.account_id = shop_id
            Configuration.secret_key = secret_key
        return cls._instance

    def set_bot(self, bot):
        """Установка бота для отправки уведомлений"""
        self._bot = bot

    def create_payment(self, 
                       amount: float, 
                       currency: str,
                       description: str, 
                       return_url: str,
                       user_id: int,):
        idempotence_key = str(uuid.uuid4())

        payment = Payment.create({
            "amount": {
                "value": amount,
                "currency": currency
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "description": description,
            "capture": True,
        }, idempotence_key)

        # Save payment to database
        db_payment = db_create_payment(
            payment_id=payment.id,
            amount=float(payment.amount.value),
            currency=payment.amount.currency,
            status='pending',
            user_id=user_id,
        )

        # Start payment status checker
        if self._bot:
            asyncio.create_task(self.check_payment_status(payment.id))

        return payment

    async def check_payment_status(self, payment_id: str):
        """
        Асинхронная функция для проверки статуса платежа.
        """
        while True:
            try:
                payment = Payment.find_one(payment_id)
                
                # Обрабатываем статус через handler
                if payment.status in ['succeeded', 'canceled']:
                    await handle_payment_status(payment_id, payment.status, self._bot)
                    return
                
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"Error checking payment {payment_id}: {str(e)}")
                await asyncio.sleep(20)


yookassa = YookassaService(
    shop_id=settings.YOOKASSA_SHOP_ID,
    secret_key=settings.YOOKASSA_SECRET_KEY)


        
