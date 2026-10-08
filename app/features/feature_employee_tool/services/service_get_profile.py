# Mocked employee-profile lookup. The 1s sleep simulates a slow downstream
# call — real latency this feature is designed to hide behind asyncio.gather.
import asyncio


async def service_get_profile(user_id: str) -> dict:
    """Mock lookup of `user_id`'s own profile (name, grade). Always returns
    the same fixed profile — a stand-in for a real HR/identity service call."""
    await asyncio.sleep(1)
    return {"name": "Jane Doe", "grade": "Senior"}
