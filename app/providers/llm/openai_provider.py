# Concrete LLMProvider backed by OpenAI. Unlike Gemini's automatic function
# calling, OpenAI's SDK has no built-in Python-callable tool execution, so
# this does the tool-call loop manually: one non-streamed call to let the
# model decide whether to call a tool, then a second streamed call (with the
# tool's result appended) to produce the final answer.
import json
from typing import Any, AsyncIterator, Callable

from openai import AsyncOpenAI


def _build_tool_schema(fn: Callable[..., Any]) -> dict:
    """Converts a zero-argument async Python callable into the JSON schema
    OpenAI's tool-calling API expects, using the function's name and
    docstring as the tool's name/description."""
    return {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": (fn.__doc__ or "").strip(),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    }


class OpenAIProvider:
    """Concrete LLMProvider backed by the OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Streams the model's reply token by token. Since OpenAI won't
        execute Python callables itself, tool use is a manual two-step: first
        a non-streamed call lets the model decide whether to call a tool and
        with what result to continue; then a second, streamed call produces
        the actual answer text using that tool result as extra context."""
        tools = tools or []
        tool_map = {fn.__name__: fn for fn in tools}
        tool_schemas = [_build_tool_schema(fn) for fn in tools] or None

        messages: list[dict] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        if tool_schemas:
            # Non-streamed on purpose: we need the complete tool_calls list
            # before we can run the tools and append their results.
            decision = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tool_schemas,
            )
            choice = decision.choices[0].message
            if choice.tool_calls:
                messages.append(choice.model_dump(exclude_unset=True))
                for call in choice.tool_calls:
                    # Our tools take no arguments (see make_employee_context_tool),
                    # so the model's requested arguments are intentionally ignored.
                    result = await tool_map[call.function.name]()
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result),
                    })

        # Final answer call, now streamed since no further tool round-trip is needed.
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=messages,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
