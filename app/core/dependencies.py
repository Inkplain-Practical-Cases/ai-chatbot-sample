# Shared singletons for providers. Built once (lru_cache) and injected via
# FastAPI's Depends() — features never construct a concrete provider themselves.
from functools import lru_cache

from app.core.config import get_settings
from app.providers.embeddings.sentence_transformers_provider import SentenceTransformersProvider
from app.providers.llm.base import LLMProvider
from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.openai_provider import OpenAIProvider
from app.providers.vectorstore.chroma_store import ChromaStore


@lru_cache
def get_embedder() -> SentenceTransformersProvider:
    """Returns the shared embedding model instance, loading its weights only
    once per process (lru_cache) instead of once per websocket connection."""
    settings = get_settings()
    return SentenceTransformersProvider(settings.embedding_model)


@lru_cache
def get_vectorstore() -> ChromaStore:
    """Returns the shared Chroma client/collection handle, opened once and
    reused across requests instead of reconnecting on every query."""
    settings = get_settings()
    return ChromaStore(path=settings.chroma_path, collection_name=settings.chroma_collection)


@lru_cache
def get_llm_provider() -> LLMProvider:
    """Returns the shared LLMProvider selected by settings.llm_provider."""
    # Swapping providers is a one-line .env change (LLM_PROVIDER=gemini|openai) —
    # no code in feature_chat depends on which concrete provider is active.
    settings = get_settings()
    if settings.llm_provider == "openai":
        return OpenAIProvider(api_key=settings.openai_api_key, model=settings.openai_model)
    return GeminiProvider(api_key=settings.gemini_api_key, model=settings.gemini_model)
