from datetime import datetime, timezone


async def current_time() -> str:
    """Get the current real world time."""
    return datetime.now(timezone.utc).astimezone().isoformat()
