# Pluggable LLM interface — features depend on this Protocol only, never on
# a concrete SDK, so the provider (Gemini/Groq/OpenAI/...) can be swapped via
# config alone (README requirement 6: "keep it pluggable").
from typing import Any, AsyncIterator, Callable, Protocol


class LLMProvider(Protocol):
    def stream_chat(
        self,
        system_prompt: str,
        user_message: str,
        tools: list[Callable[..., Any]] | None = None,
    ) -> AsyncIterator[str]: ...
