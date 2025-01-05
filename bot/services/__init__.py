"""
Модуль для инициализации сервисов
"""

async def setup_services(bot):
    """
    Инициализация всех сервисов после создания бота
    """
    from bot.services.yookassa_service import yookassa
    yookassa.set_bot(bot) 