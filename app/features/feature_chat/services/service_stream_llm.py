# Turns retrieved chunks into a system prompt and streams the LLM's answer.
# The LLM decides whether the context is relevant — a plain greeting or an
# off-topic question gets a normal reply instead of a forced RAG answer.
from typing import AsyncIterator

from app.features.feature_employee_tool.tool_get_employee_context import make_employee_context_tool
from app.providers.llm.base import LLMProvider
from app.providers.vectorstore.base import Chunk

SYSTEM_PROMPT_TEMPLATE = """You are a helpful company assistant answering questions about \
internal policy documents. Use the CONTEXT below when it is relevant to the user's question — \
document content is already provided there in full; never invent a tool to fetch a document, \
policy, or file. If the context doesn't answer the question, or the message is just small \
talk, respond naturally without forcing the context in. Always cite the source file in \
parentheses when you use information from the context, e.g. (leave_policy.pdf).

The ONLY tool available to you is get_employee_context, which takes no arguments and returns \
the current user's own profile, manager, and team. Call it only when the question is about \
the user themselves (their grade, manager, or team) — never for anything else, and never any \
other tool name.

CONTEXT:
{context}
"""


def _build_system_prompt(chunks: list[Chunk]) -> str:
    """Renders SYSTEM_PROMPT_TEMPLATE with the retrieved chunks formatted as
    labeled context blocks, or a placeholder if RBAC filtering left none."""
    if not chunks:
        context = "(no matching documents were found for this user's access level)"
    else:
        context = "\n\n".join(f"[{c.source_file} p.{c.page}]\n{c.text}" for c in chunks)
    return SYSTEM_PROMPT_TEMPLATE.format(context=context)


async def service_stream_llm(
    user_message: str,
    chunks: list[Chunk],
    llm: LLMProvider,
    user_id: str,
) -> AsyncIterator[str]:
    """Builds the RAG system prompt from `chunks` and streams the LLM's reply
    token by token. `user_id` is bound into the employee-context tool so the
    LLM can only ever fetch the current user's own data (see tool_get_employee_context.py)."""
    system_prompt = _build_system_prompt(chunks)
    employee_context_tool = make_employee_context_tool(user_id)
    async for token in llm.stream_chat(system_prompt, user_message, tools=[employee_context_tool]):
        yield token
