from typing import Any, Awaitable, Callable, Dict
from datetime import datetime, timedelta
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject
from aiogram.fsm.context import FSMContext
from bot.states.consultation import ConsultationStates

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 5):
        self.rate_limit = rate_limit
        self.user_timestamps = {}

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]) -> Any:
        user_id = event.from_user.id
        current_time = datetime.now()

        if user_id in self.user_timestamps:
            last_time = self.user_timestamps[user_id]
            time_diff = current_time - last_time
            if time_diff < timedelta(seconds=self.rate_limit):
                return await event.answer(f'Подождите {self.rate_limit - time_diff.seconds} секунд перед отправкой следующего сообщения.')

        self.user_timestamps[user_id] = current_time
        return await handler(event, data)

class AdminMessageThrottlingMiddleware(BaseMiddleware):
    def __init__(self, cooldown_minutes: int = 30):
        self.cooldown = timedelta(minutes=cooldown_minutes)
        self.user_slot_timestamps = {}

    async def __call__(
            self,
            handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
            event: Message,
            data: Dict[str, Any]) -> Any:
        
        state: FSMContext = data.get('state')
        if not state:
            return await handler(event, data)
            
        current_state = await state.get_state()
        if current_state != ConsultationStates.waiting_for_message.state:
            return await handler(event, data)

        state_data = await state.get_data()
        booking_id = state_data.get('booking_id')
        if not booking_id:
            return await handler(event, data)

        user_id = event.from_user.id
        current_time = datetime.now()
        
        key = f"{user_id}_{booking_id}"
        
        if key in self.user_slot_timestamps:
            last_time = self.user_slot_timestamps[key]
            time_diff = current_time - last_time
            
            if time_diff < self.cooldown:
                minutes_left = int((self.cooldown - time_diff).total_seconds() / 60)
                await state.clear()
                return await event.answer(
                    f"⚠️ Вы уже отправляли сообщение по этой консультации.\n"
                    f"Повторно отправить можно через {minutes_left} минут."
                )

        self.user_slot_timestamps[key] = current_time
        return await handler(event, data)
