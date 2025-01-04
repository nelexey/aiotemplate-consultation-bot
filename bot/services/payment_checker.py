import asyncio
from datetime import datetime, timedelta, UTC
from typing import Optional

from bot.services.yookassa import YooKassaService
from bot.database.methods.update import update_payment_status, update_slot_status
from bot.database.methods.read import get_payment_by_id, get_slot_by_id, get_user
from bot.misc.env import settings

async def check_payment_status_loop(
    payment_id: str,
    slot_id: int,
    chat_id: int,
    bot,
    timeout_minutes: int = 10
) -> None:
    """
    Асинхронная функция для проверки статуса платежа.
    
    Args:
        payment_id: ID платежа в YooKassa
        slot_id: ID слота
        chat_id: ID чата пользователя в Telegram
        bot: Объект бота для отправки сообщений
        timeout_minutes: Время ожидания оплаты в минутах
    """
    start_time = datetime.now(UTC)
    yookassa_service = YooKassaService()
    
    while True:
        # Проверяем, не истекло ли время
        if datetime.now(UTC) - start_time > timedelta(minutes=timeout_minutes):
            # Время истекло
            await bot.send_message(
                chat_id,
                "❌ Время ожидания оплаты истекло.\n"
                "Бронирование отменено."
            )
            # Обновляем статус слота
            update_slot_status(slot_id, 'available')
            # Обновляем статус платежа
            update_payment_status(payment_id, 'expired', None)
            break

        try:
            # Проверяем статус платежа
            payment = await yookassa_service.check_payment(payment_id)
            status = payment.status

            if status == 'succeeded':
                # Получаем информацию о платеже
                payment_info = get_payment_by_id(payment_id)
                if not payment_info:
                    print(f"Payment {payment_id} not found in database")
                    break

                # Платеж успешен
                update_slot_status(slot_id, 'booked', client_id=payment_info.user_id)
                update_payment_status(payment_id, status, datetime.now(UTC))
                
                slot = get_slot_by_id(slot_id)
                await bot.send_message(
                    chat_id,
                    "✅ Оплата прошла успешно!\n"
                    "✅ Вы успешно записались на консультацию!\n\n"
                    f"📅 Дата и время: {slot.datetime.strftime('%d.%m.%Y %H:%M')}"
                )
                break
                
            elif status == 'canceled':
                # Платеж отменен
                update_slot_status(slot_id, 'available')
                update_payment_status(payment_id, status, None)
                
                await bot.send_message(
                    chat_id,
                    "❌ Платеж был отменен.\n"
                    "Бронирование отменено."
                )
                break
                
            # Если статус все еще pending, ждем и проверяем снова
            await asyncio.sleep(1)  # Проверяем каждые 30 секунд
            
        except Exception as e:
            print(f"Error checking payment {payment_id}: {str(e)}")
            await asyncio.sleep(30)  # В случае ошибки тоже ждем 30 секунд 