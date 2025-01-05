from yookassa import Payment
import uuid
import asyncio
from bot.database.methods.create import create_payment as db_create_payment
from bot.misc.env import settings

class YookassaService:
    _instance = None

    def __new__(cls, shop_id: str = None, secret_key: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.shop_id = shop_id
            cls._instance.secret_key = secret_key
            Payment.configure(shop_id, secret_key)
        return cls._instance

    def create_payment(self, 
                       amount: float, 
                       currency: str,
                       description: str, 
                       return_url: str,
                       user_id: int,
                       slot_id: int):
        idempotence_key = str(uuid.uuid4())

        """
        1. Создать объект платежа
        2. Сохранить платеж в базу данных
        3. Запустить асинхронную функцию проверки платежа
        4. Вернуть пользователю ссылку на оплату
        """

        payment = Payment.create({
            "amount": {
                "value": amount,
                "currency": currency
            },
            "payment_method_data": {
                "type": "bank_card"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
            },
            "description": description
        }, idempotence_key)

        # Save payment to database
        db_payment = db_create_payment(
            payment_id=payment.id,
            amount=float(payment.amount.value),
            currency=payment.amount.currency,
            status='pending',
            user_id=user_id,
            slot_id=slot_id
        )

        # Start payment status checker
        asyncio.create_task(self.check_payment_status(payment.id))

        return payment

    async def check_payment_status(self, payment_id: str):
        """
        Асинхронная функция для проверки статуса платежа.
        Запускается в отдельной таске для каждого платежа.
        """
        while True:
            try:
                payment = Payment.find_one(payment_id)
                
                match payment.status:
                    case "pending":
                        print(f"Payment {payment_id} is still pending")
                    case "waiting_for_capture":
                        print(f"Payment {payment_id} is waiting for capture")
                    case "succeeded":
                        print(f"Payment {payment_id} succeeded!")
                        return  # Завершаем проверку при успешной оплате
                    case "canceled":
                        print(f"Payment {payment_id} was canceled")
                        return  # Завершаем проверку при отмене
                    case _:
                        print(f"Payment {payment_id} has unknown status: {payment.status}")
                
                await asyncio.sleep(2)
                print("Waiting for 2 seconds")
                
            except Exception as e:
                print(f"Error checking payment {payment_id}: {str(e)}")
                await asyncio.sleep(20)


yookassa = YookassaService(
    shop_id=settings.YOOKASSA_SHOP_ID,
    secret_key=settings.YOOKASSA_SECRET_KEY
)


        
