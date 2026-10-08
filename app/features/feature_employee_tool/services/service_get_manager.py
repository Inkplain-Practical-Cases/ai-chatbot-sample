# Mocked manager lookup. See service_get_profile.py for why the sleep exists.
import asyncio


async def service_get_manager(user_id: str) -> dict:
    """Mock lookup of `user_id`'s manager. In a real system this would call
    an HR/identity service; here it always returns the same fixed manager."""
    await asyncio.sleep(1)
    return {"manager": "John Smith"}
