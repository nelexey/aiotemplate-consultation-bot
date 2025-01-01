from aiogram import Router
from typing import Tuple

from .commands import commands_router
from .consultation import admin_consultation_router

def register_handlers(up_router: Router) -> Tuple[Router, ...]:
    return (
        commands_router,
        admin_consultation_router,
    )