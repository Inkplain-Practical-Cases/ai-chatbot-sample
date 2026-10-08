# The parallel tool call required by the assignment: profile, manager, and
# team are each a ~1s mock call, run concurrently with asyncio.gather so the
# total wall time is ~1s, not ~3s.
#
# make_employee_context_tool() binds user_id to a zero-argument closure before
# handing it to the LLM as a callable tool. This is deliberate: letting the
# model supply user_id itself would mean trusting the LLM to pick which
# employee's data to fetch, which breaks the RBAC identity boundary set at
# auth time. The tool can only ever look up the connection's own user.
import asyncio
from typing import Callable, Coroutine

from app.features.feature_employee_tool.services.service_get_manager import service_get_manager
from app.features.feature_employee_tool.services.service_get_profile import service_get_profile
from app.features.feature_employee_tool.services.service_get_team import service_get_team


async def tool_get_employee_context(user_id: str) -> dict:
    """Fetches profile, manager, and team for `user_id` concurrently and
    merges them into one dict. Runs in ~1s total instead of ~3s because the
    three mock calls are gathered rather than awaited one after another."""
    profile, manager, team = await asyncio.gather(
        service_get_profile(user_id),
        service_get_manager(user_id),
        service_get_team(user_id),
    )
    return {**profile, **manager, **team}


def make_employee_context_tool(user_id: str) -> Callable[[], Coroutine[None, None, dict]]:
    """Returns a zero-argument async closure over `user_id`, suitable for
    handing straight to an LLMProvider as a callable tool. Binding user_id
    here (rather than making it a tool argument) is what keeps the LLM from
    ever being able to request another user's data."""

    async def get_employee_context() -> dict:
        """Returns the current user's own profile (name, grade), manager, and
        team info. Call this when the user asks something personal about
        themselves, e.g. their grade, who their manager is, or their team."""
        return await tool_get_employee_context(user_id)

    return get_employee_context
