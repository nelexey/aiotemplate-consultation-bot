from datetime import datetime, UTC
from bot.database.methods import update, read

async def handle_payment_status(payment_id: str, status: str, bot):
    """
    Обработчик статусов платежа
    """
    payment = read.get_payment(payment_id)
    if not payment or not payment.user:
        return

    match status:
        case "succeeded":
            # Обновляем статус платежа
            if not update.update_payment_status(payment_id, 'succeeded', datetime.now(UTC)):
                return

            # Обновляем баланс пользователя
            new_balance = float(payment.user.balance) + float(payment.amount)
            if not update.update_user_balance(payment.user.id, new_balance):
                return

            # Уведомляем пользователя
            await bot.send_message(
                payment.user.chat_id,
                f"✅ Оплата успешно произведена!\n"
                f"Сумма: {payment.amount} {payment.currency}\n"
                f"Ваш текущий баланс: {new_balance} {payment.currency}"
            )

        case "canceled":
            # Обновляем статус платежа
            if not update.update_payment_status(payment_id, 'canceled'):
                return

            # Уведомляем пользователя
            await bot.send_message(
                payment.user.chat_id,
                f"❌ Платеж отменен.\n"
                f"Сумма: {payment.amount} {payment.currency}\n"
                f"Попробуйте снова или выберите другой способ оплаты."
            ) 