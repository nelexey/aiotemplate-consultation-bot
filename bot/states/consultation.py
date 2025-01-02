from aiogram.fsm.state import State, StatesGroup

class ConsultationStates(StatesGroup):
    waiting_for_message = State() 