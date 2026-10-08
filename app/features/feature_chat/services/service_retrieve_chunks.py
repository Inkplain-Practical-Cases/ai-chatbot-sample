# Embeds the user's question and queries the vector store with the RBAC
# filter applied at the DB layer (see ChromaStore.query). Both the embedding
# model and Chroma's local client are sync/CPU-bound, so each call is pushed
# to a worker thread with asyncio.to_thread — never awaited directly, which
# would block every other connection's message loop.
import asyncio

from app.providers.embeddings.sentence_transformers_provider import SentenceTransformersProvider
from app.providers.vectorstore.base import Chunk
from app.providers.vectorstore.chroma_store import ChromaStore


async def service_retrieve_chunks(
    text: str,
    department: str,
    level: int,
    embedder: SentenceTransformersProvider,
    store: ChromaStore,
    limit: int = 5,
) -> list[Chunk]:
    """Embeds `text` and returns up to `limit` chunks the (department, level)
    pair is allowed to see, most relevant first. The RBAC check itself happens
    inside store.query's `where` filter, not here."""
    embeddings = await asyncio.to_thread(embedder.embed, [text])
    query_embedding = embeddings[0]
    return await asyncio.to_thread(store.query, query_embedding, department, level, limit)
