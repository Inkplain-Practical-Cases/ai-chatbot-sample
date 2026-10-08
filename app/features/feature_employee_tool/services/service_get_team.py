# Mocked team lookup. See service_get_profile.py for why the sleep exists.
import asyncio


async def service_get_team(user_id: str) -> dict:
    """Mock lookup of `user_id`'s team. Always returns the same fixed team —
    a stand-in for a real HR/identity service call."""
    await asyncio.sleep(1)
    return {"team_size": 8, "team_name": "Platform"}
