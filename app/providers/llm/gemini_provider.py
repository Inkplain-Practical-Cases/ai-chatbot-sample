# Concrete LLMProvider backed by Google Gemini (free tier, gemini-3.6-flash).
# Uses the async chats API (not generate_content_stream directly) because
# Gemini's automatic function calling — used for the employee-context tool —
# is only supported there: it detects a plain Python function's signature/
# docstring, calls it when the model requests it, then continues the stream.
from typing import Any, AsyncIterator, Callable

from google import genai
from google.genai import types


class GeminiProvider:
    """Concrete LLMProvider backed by the Gemini API."""

    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]:
        """Streams the model's reply token by token. `tools` (plain async
        Python callables) are passed straight to Gemini's automatic function
        calling, which invokes them itself mid-stream when the model decides to."""
        # A fresh chat session per call — no conversation history is kept
        # across messages, each question is answered independently.
        chat = self._client.aio.chats.create(
            model=self._model,
            config=types.GenerateContentConfig(system_instruction=system_prompt, tools=tools or []),
        )
        stream = await chat.send_message_stream(user_message)
        async for chunk in stream:
            if chunk.text:
                yield chunk.text
