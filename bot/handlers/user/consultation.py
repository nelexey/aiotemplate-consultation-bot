from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from bot.database.methods.slots import get_available_slots, book_slot, get_slot_by_id, get_user_bookings, check_user_booking_limit, cancel_booking
from bot.keyboards.inline.consultation import create_slots_keyboard, create_confirm_keyboard, create_bookings_keyboard, create_booking_details_keyboard
from bot.database.methods.users import get_user_by_chat_id
from bot.misc.env import settings
from bot.middlewares.throttling import AdminMessageThrottlingMiddleware
from bot.states.consultation import ConsultationStates
from bot.services.yookassa import YooKassaService
from bot.database.methods.create import create_payment
from bot.keyboards.inline.payment import create_payment_status_keyboard

consultation_router = Router()
consultation_router.message.middleware(AdminMessageThrottlingMiddleware(cooldown_minutes=30))

@consultation_router.message(Command("schedule"))
async def show_schedule(message: Message):
    from_date = datetime.now()
    to_date = from_date + timedelta(days=14)
    
    available_slots = get_available_slots(from_date, to_date)
    if not available_slots:
        await message.answer("К сожалению, нет доступных слотов для записи.")
        return
    
    keyboard = await create_slots_keyboard(available_slots, page=1)
    await message.answer("Выберите удобное время для консультации:", reply_markup=keyboard)

@consultation_router.callback_query(F.data.startswith("book_"))
async def process_booking(callback: CallbackQuery):
    slot_id = int(callback.data.split("_")[1])
    keyboard = await create_confirm_keyboard(slot_id)
    await callback.message.edit_text(
        "Подтвердите запись на консультацию:",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("confirm_"))
async def confirm_booking(callback: CallbackQuery, state: FSMContext):
    slot_id = int(callback.data.split("_")[1])
    user = get_user_by_chat_id(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text("❌ Произошла ошибка. Попробуйте начать сначала с /start")
        return
    
    if not check_user_booking_limit(user.id):
        await callback.message.edit_text(
            f"❌ Превышен лимит бронирований. Максимально доступно: {settings.BOOKING_LIMIT} активных записей."
        )
        return

    # Проверяем, не занят ли слот
    slot = get_slot_by_id(slot_id)
    if not slot or slot.status != 'available':
        await callback.message.edit_text("❌ Извините, этот слот уже занят.")
        return

    try:
        # Создаем платеж в ЮKassa
        yookassa_service = YooKassaService()
        payment_id, payment_url = await yookassa_service.create_payment(user.id, slot_id)

        # Сохраняем информацию о платеже в базе данных
        create_payment(
            payment_id=payment_id,
            amount=float(settings.yookassa_config['price']),
            currency=settings.yookassa_config['currency'],
            status='pending',
            user_id=user.id,
            slot_id=slot_id
        )

        # Сохраняем ID платежа в состоянии для последующей проверки
        await state.set_state(ConsultationStates.waiting_for_payment)
        await state.update_data(payment_id=payment_id, slot_id=slot_id)

        print(payment_url)

        # Отправляем пользователю ссылку на оплату
        keyboard = create_payment_status_keyboard(payment_id, payment_url)
        await callback.message.edit_text(
            "💳 Для подтверждения записи необходимо оплатить консультацию\n\n"
            f"💰 Сумма к оплате: {settings.yookassa_config['price']} {settings.yookassa_config['currency']}\n"
            f"🕐 Время на оплату: 30 минут\n\n"
            "Нажмите на кнопку ниже, чтобы перейти к оплате:",
            reply_markup=keyboard
        )

    except Exception as e:
        print(f"Error creating payment: {str(e)}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании платежа. Пожалуйста, попробуйте позже."
        )

@consultation_router.message(Command("my_bookings"))
async def show_my_bookings(message: Message):
    user = get_user_by_chat_id(message.from_user.id)
    if not user:
        await message.answer("❌ Произошла ошибка. Попробуйте начать сначала с /start")
        return
        
    bookings = get_user_bookings(user.id)
    active_bookings = len(bookings)
    
    if not bookings:
        await message.answer(
            f"У вас нет предстоящих консультаций.\n"
            f"Доступно записей: {settings.BOOKING_LIMIT}"
        )
        return
    
    keyboard = await create_bookings_keyboard(bookings, page=1)
    await message.answer(
        f"📅 Ваши предстоящие консультации ({active_bookings}/{settings.BOOKING_LIMIT}):",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("booking_details_"))
async def show_booking_details(callback: CallbackQuery):
    booking_id = int(callback.data.split("_")[2])
    slot = get_slot_by_id(booking_id)
    
    if not slot:
        await callback.answer("Консультация не найдена")
        return
        
    time_until = slot.datetime - datetime.now()
    hours_left = int(time_until.total_seconds() / 3600)
    
    if hours_left < 1:
        time_info = f"через {int(time_until.total_seconds() / 60)} минут"
    else:
        time_info = f"через {hours_left} часов"
    
    keyboard = await create_booking_details_keyboard(booking_id)
    await callback.message.edit_text(
        f"📅 Консультация {slot.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        f"⏳ Начнется {time_info}\n\n"
        "Выберите действие:",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("cancel_booking_"))
async def process_booking_cancellation(callback: CallbackQuery):
    booking_id = int(callback.data.split("_")[2])
    user = get_user_by_chat_id(callback.from_user.id)
    
    if await cancel_booking(booking_id, callback.bot):
        bookings = get_user_bookings(user.id)
        if bookings:
            keyboard = await create_bookings_keyboard(bookings, page=1)
            await callback.message.edit_text(
                f"✅ Бронирование отменено\n\n"
                f"📅 Ваши предстоящие консультации ({len(bookings)}/{settings.BOOKING_LIMIT}):",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                "✅ Бронирование отменено\n\n"
                f"У вас нет предстоящих консультаций.\n"
                f"Доступно записей: {settings.BOOKING_LIMIT}"
            )
    else:
        await callback.answer("❌ Не удалось отменить бронирование")

@consultation_router.callback_query(F.data == "back_to_bookings")
async def back_to_bookings_list(callback: CallbackQuery):
    user = get_user_by_chat_id(callback.from_user.id)
    bookings = get_user_bookings(user.id)
    keyboard = await create_bookings_keyboard(bookings, page=1)
    
    await callback.message.edit_text(
        f"📅 Ваши предстоящие консультации ({len(bookings)}/{settings.BOOKING_LIMIT}):",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("bookings_page_"))
async def process_bookings_page(callback: CallbackQuery):
    page = int(callback.data.split("_")[2])
    user = get_user_by_chat_id(callback.from_user.id)
    bookings = get_user_bookings(user.id)
    
    keyboard = await create_bookings_keyboard(bookings, page=page)
    await callback.message.edit_reply_markup(reply_markup=keyboard) 

@consultation_router.callback_query(F.data.startswith("cancel_"))
async def cancel_booking_creation(callback: CallbackQuery):
    from_date = datetime.now()
    to_date = from_date + timedelta(days=14)
    
    available_slots = get_available_slots(from_date, to_date)
    keyboard = await create_slots_keyboard(available_slots, page=1)
    
    await callback.message.edit_text(
        "Выберите удобное время для консультации:",
        reply_markup=keyboard
    ) 

@consultation_router.callback_query(F.data.startswith("write_admin_"))
async def process_write_admin(callback: CallbackQuery, state: FSMContext):
    booking_id = int(callback.data.split("_")[2])
    slot = get_slot_by_id(booking_id)
    
    if not slot:
        await callback.answer("Консультация не найдена")
        return
        
    await state.update_data(booking_id=booking_id)
    await state.set_state(ConsultationStates.waiting_for_message)
    
    await callback.message.edit_text(
        "📝 Пожалуйста, напишите ваше сообщение для администратора.\n"
        "Оно будет отправлено вместе с информацией о вашей консультации."
    )

@consultation_router.message(StateFilter(ConsultationStates.waiting_for_message))
async def process_admin_message(message: Message, state: FSMContext):
    data = await state.get_data()
    booking_id = data.get("booking_id")
    slot = get_slot_by_id(booking_id)
    
    if not slot:
        await message.answer("❌ Произошла ошибка. Консультация не найдена.")
        await state.clear()
        return
        
    user_message = message.text
    user = message.from_user
    client_info = f"{user.first_name}"
    if user.last_name:
        client_info += f" {user.last_name}"
    if user.username:
        client_info += f" (@{user.username})"
    
    for admin_id in settings.admin_ids:
        try:
            await message.bot.send_message(
                admin_id,
                f"💬 Новое сообщение от {client_info}\n"
                f"📅 Слот: {slot.datetime.strftime('%d.%m.%Y %H:%M')}\n"
                f"📝 Сообщение:\n{user_message}"
            )
        except Exception as e:
            print(f"Error sending message to admin {admin_id}: {str(e)}")
    
    await message.answer("✅ Ваше сообщение отправлено администраторам!")
    await state.clear()
    
    keyboard = await create_booking_details_keyboard(booking_id)
    await message.answer(
        f"📅 Консультация {slot.datetime.strftime('%d.%m.%Y %H:%M')}\n"
        "Выберите действие:",
        reply_markup=keyboard
    ) 

@consultation_router.callback_query(F.data.startswith("check_payment_"))
async def check_payment_status(callback: CallbackQuery, state: FSMContext):
    payment_id = callback.data.split("_")[2]
    
    try:
        # Получаем информацию о платеже из YooKassa
        yookassa_service = YooKassaService()
        payment_status = await yookassa_service.check_payment_status(payment_id)
        
        if payment_status == "succeeded":
            # Получаем данные из состояния
            data = await state.get_data()
            slot_id = data.get("slot_id")
            user = get_user_by_chat_id(callback.from_user.id)
            
            # Бронируем слот
            if book_slot(slot_id, user.id):
                slot = get_slot_by_id(slot_id)
                time_until = slot.datetime - datetime.now()
                
                await callback.message.edit_text(
                    "✅ Оплата прошла успешно!\n"
                    "✅ Вы успешно записались на консультацию!"
                )
                
                if time_until <= timedelta(hours=1):
                    minutes_left = int(time_until.total_seconds() / 60)
                    await callback.message.answer(
                        f"⚡️ Ваша консультация начнется через {minutes_left} минут, "
                        f"в {slot.datetime.strftime('%H:%M')}!"
                    )
                
                # Очищаем состояние
                await state.clear()
            else:
                await callback.message.edit_text(
                    "❌ Оплата прошла успешно, но слот уже занят.\n"
                    "Пожалуйста, выберите другое время."
                )
                # TODO: Добавить логику возврата средств
        
        elif payment_status == "pending":
            await callback.answer(
                "⏳ Оплата все еще в обработке. Пожалуйста, подождите или попробуйте проверить позже.",
                show_alert=True
            )
        
        elif payment_status == "canceled":
            await callback.message.edit_text(
                "❌ Платеж был отменен.\n"
                "Пожалуйста, выберите время консультации заново."
            )
            await state.clear()
        
        else:
            await callback.answer(
                "❌ Неизвестный статус платежа. Пожалуйста, обратитесь в поддержку.",
                show_alert=True
            )
    
    except Exception as e:
        print(f"Error checking payment status: {str(e)}")
        await callback.answer(
            "❌ Произошла ошибка при проверке статуса платежа. Пожалуйста, попробуйте позже.",
            show_alert=True
        )

@consultation_router.callback_query(F.data == "cancel_payment")
async def cancel_payment(callback: CallbackQuery, state: FSMContext):
    try:
        # Получаем данные из состояния
        data = await state.get_data()
        payment_id = data.get("payment_id")
        
        if payment_id:
            # Отменяем платеж в YooKassa
            yookassa_service = YooKassaService()
            await yookassa_service.cancel_payment(payment_id)
        
        # Очищаем состояние
        await state.clear()
        
        # Возвращаем пользователя к выбору времени
        from_date = datetime.now()
        to_date = from_date + timedelta(days=14)
        available_slots = get_available_slots(from_date, to_date)
        keyboard = await create_slots_keyboard(available_slots, page=1)
        
        await callback.message.edit_text(
            "❌ Платеж отменен.\n"
            "Выберите удобное время для консультации:",
            reply_markup=keyboard
        )
    
    except Exception as e:
        print(f"Error canceling payment: {str(e)}")
        await callback.answer(
            "❌ Произошла ошибка при отмене платежа. Пожалуйста, попробуйте позже.",
            show_alert=True
        ) 