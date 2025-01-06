from aiogram import Router
from typing import Tuple

from .commands import commands_router
from .consultation import consultation_router
from .balance import router as balance_router

def register_handlers(up_router: Router, **kwargs) -> Tuple[Router, ...]:
    return (
        commands_router,
        consultation_router,
        balance_router,
    )