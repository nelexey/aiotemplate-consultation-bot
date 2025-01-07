from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta

from bot.database.methods.read import get_available_slots, get_slot_by_id, get_user_bookings, check_user_booking_limit
from bot.database.methods.update import book_slot, cancel_booking, release_slot, deduct_consultation_fee, refund_consultation_fee
from bot.database.methods.read import get_user_by_chat_id
from bot.keyboards.inline.consultation import (
    create_slots_keyboard,
    create_confirm_keyboard,
    create_bookings_keyboard,
    create_booking_details_keyboard,
    get_no_bookings_keyboard,
    get_success_booking_keyboard
)
from bot.keyboards.inline.menu import get_back_to_menu_keyboard
from bot.misc.env import settings
from bot.middlewares.throttling import AdminMessageThrottlingMiddleware
from bot.states.consultation import ConsultationStates
from bot.services.notifications import notify_admins_booking_cancelled

consultation_router = Router()
consultation_router.message.middleware(AdminMessageThrottlingMiddleware(cooldown_minutes=30))

@consultation_router.message(Command("schedule"))
async def show_schedule(message: Message, edit: bool = False):
    from_date = datetime.now()
    to_date = from_date + timedelta(days=14)
    
    available_slots = get_available_slots(from_date, to_date)
    if not available_slots:
        text = "К сожалению, нет доступных слотов для записи."
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return
    
    keyboard = await create_slots_keyboard(available_slots, page=1)
    
    text = "Выберите удобное время для консультации:"
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

@consultation_router.callback_query(F.data.startswith("book_"))
async def process_booking(callback: CallbackQuery):
    slot_id = int(callback.data.split("_")[1])
    keyboard = await create_confirm_keyboard(slot_id)
    await callback.message.edit_text(
        "Подтвердите запись на консультацию:",
        reply_markup=keyboard
    )

@consultation_router.callback_query(F.data.startswith("confirm_"))
async def confirm_booking(callback: CallbackQuery):
    slot_id = int(callback.data.split("_")[1])
    user = get_user_by_chat_id(callback.from_user.id)
    
    if not user:
        await callback.message.edit_text("❌ Произошла ошибка. Попробуйте начать сначала с /start")
        return
    
    slot = get_slot_by_id(slot_id)
    if not slot:
        await callback.message.edit_text("❌ Слот не найден.")
        return
    
    # Check if user has enough balance
    if user.balance < slot.price:
        from bot.keyboards.inline.balance import get_balance_keyboard
        keyboard = get_balance_keyboard()
        await callback.message.edit_text(
            f"❌ Недостаточно средств на балансе.\n"
            f"Стоимость консультации: {slot.price} {settings.CURRENCY_SYMBOL}\n"
            f"Ваш баланс: {user.balance} {settings.CURRENCY_SYMBOL}",
            reply_markup=keyboard
        )
        return
    
    if not check_user_booking_limit(user.id, settings.BOOKING_LIMIT):
        await callback.message.edit_text(
            f"❌ Превышен лимит бронирований. Максимально доступно: {settings.BOOKING_LIMIT} активных записей."
        )
        return
    
    if not deduct_consultation_fee(user.id, float(slot.price)):
        await callback.message.edit_text("❌ Ошибка при списании средств. Попробуйте позже.")
        return
        
    if book_slot(slot_id, user.id):
        slot = get_slot_by_id(slot_id)
        time_until = slot.datetime - datetime.now()
        
        keyboard = get_success_booking_keyboard()
        await callback.message.edit_text(
            f"✅ Вы успешно записались на консультацию!\n"
            f"💰 С баланса списано: {slot.price} {settings.CURRENCY_SYMBOL}",
            reply_markup=keyboard
        )
        
        if time_until <= timedelta(hours=1):
            minutes_left = int(time_until.total_seconds() / 60)
            await callback.message.answer(
                f"⚡️ Ваша консультация начнется через {minutes_left} минут, "
                f"в {slot.datetime.strftime('%H:%M')}!"
            )
    else:
        refund_consultation_fee(user.id, float(slot.price))
        await callback.message.edit_text("❌ Извините, этот слот уже занят.")

@consultation_router.message(Command("my_bookings"))
async def show_my_bookings(message: Message, edit: bool = False):
    user = get_user_by_chat_id(message.chat.id)
    if not user:
        text = "❌ Произошла ошибка. Попробуйте начать сначала с /start"
        if edit:
            await message.edit_text(text)
        else:
            await message.answer(text)
        return
        
    bookings = get_user_bookings(user.id)
    active_bookings = len(bookings)
    
    if not bookings:
        text = (f"У вас нет предстоящих консультаций.\n"
                f"Доступно записей: {settings.BOOKING_LIMIT}")
        keyboard = get_no_bookings_keyboard()
        if edit:
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)
        return
    
    keyboard = await create_bookings_keyboard(bookings, page=1)
    
    text = f"📅 Ваши предстоящие консультации ({active_bookings}/{settings.BOOKING_LIMIT}):"
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)

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
    slot = get_slot_by_id(booking_id)
    
    if not slot:
        await callback.answer("❌ Бронирование не найдено")
        return
        
    client_info = f"@{user.username}" if user.username else f"ID: {user.chat_id}"
    time_until = slot.datetime - datetime.now()
    
    # Если до консультации больше 24 часов - возвращаем полную стоимость
    should_refund = time_until > timedelta(hours=24)
    success = release_slot(booking_id) if should_refund else cancel_booking(booking_id)
    
    if success:
        refund_amount = float(slot.price) if should_refund else 0
        if refund_amount > 0:
            refund_consultation_fee(user.id, refund_amount)
            refund_message = f"\n💰 Возвращено на баланс: {refund_amount} {settings.CURRENCY_SYMBOL}"
        else:
            refund_message = "\n❗️ При отмене менее чем за 24 часа стоимость не возвращается"
        
        await notify_admins_booking_cancelled(callback.bot, slot.datetime, client_info)
        
        bookings = get_user_bookings(user.id)
        if bookings:
            keyboard = await create_bookings_keyboard(bookings, page=1)
            await callback.message.edit_text(
                f"✅ Бронирование отменено{refund_message}\n\n"
                f"📅 Ваши предстоящие консультации ({len(bookings)}/{settings.BOOKING_LIMIT}):",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                f"✅ Бронирование отменено{refund_message}\n\n"
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