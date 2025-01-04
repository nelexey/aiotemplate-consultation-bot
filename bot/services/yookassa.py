from yookassa import Configuration, Payment as YooPayment
from datetime import datetime, UTC

from bot.misc.env import settings
from bot.database.methods.create import create_payment
from bot.database.methods.read import get_payment_by_slot
from bot.database.methods.update import update_payment_status
from bot.database.methods.delete import delete_payment

class YooKassaService:
    def __init__(self):
        config = settings.yookassa_config
        Configuration.account_id = config['shop_id']
        Configuration.secret_key = config['secret_key']

    async def create_payment(self, user_id: int, slot_id: int) -> tuple[str, str]:
        """Создает платеж и возвращает (payment_id, URL для оплаты)"""
        config = settings.yookassa_config
        payment = YooPayment.create({
            "amount": {
                "value": str(config['price']),
                "currency": config['currency']
            },
            "confirmation": {
                "type": "redirect",
                "return_url": config['return_url']
            },
            "capture": True,
            "description": f"Оплата консультации (слот #{slot_id})",
            "metadata": {
                "user_id": user_id,
                "slot_id": slot_id
            }
        })

        return payment.id, payment.confirmation.confirmation_url

    async def process_notification(self, payment_data: dict) -> bool:
        """Обрабатывает уведомление от ЮKassa"""
        payment_id = payment_data['object']['id']
        status = payment_data['object']['status']
        paid_at = datetime.now(UTC) if status == 'succeeded' else None
        
        return update_payment_status(payment_id, status, paid_at)

    async def check_payment(self, payment_id: str) -> dict:
        """Проверяет статус платежа"""
        return YooPayment.find_one(payment_id)
