# Pluggable embedding interface — features depend on this, never on a
# concrete embedding library, so the provider can be swapped via config alone.
from typing import Protocol


class EmbeddingProvider(Protocol):
    def embed(self, texts: list[str]) -> list[list[float]]: ...
