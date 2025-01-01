async def register_models() -> None:
    """Register all database models."""
    from .user import User
    from .slot import TimeSlot