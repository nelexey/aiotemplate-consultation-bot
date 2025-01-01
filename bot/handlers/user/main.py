from aiogram import Router
from typing import Tuple

from .commands import commands_router
from .consultation import consultation_router

def register_handlers(up_router: Router, **kwargs) -> Tuple[Router, ...]:
    return (
        commands_router,
        consultation_router,
    )