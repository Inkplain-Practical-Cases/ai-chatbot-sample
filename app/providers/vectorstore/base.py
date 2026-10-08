# Pluggable vector store interface. Both feature_ingest (writes) and
# feature_chat (reads, with RBAC filtering) depend on this Protocol only —
# never on a concrete Chroma/Qdrant class — so the store can be swapped.
from typing import Protocol

from pydantic import BaseModel


class Chunk(BaseModel):
    """One retrievable unit: chunk text plus the RBAC/source metadata
    required by README.md (department, access_level, source_file, page)."""
    id: str
    text: str
    department: str
    access_level: int
    source_file: str
    page: int


class VectorStore(Protocol):
    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None: ...

    def query(
        self,
        query_embedding: list[float],
        department: str,
        level: int,
        limit: int = 5,
    ) -> list[Chunk]: ...
