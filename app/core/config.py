# App-wide settings, read once from .env. Every feature reads secrets/config
# from here instead of calling os.getenv() directly.
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration for the app, loaded from environment variables /
    .env. Fields with no default (jwt_secret) are required — pydantic-settings
    raises at startup if they're missing, instead of failing later at first use."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Secret used to verify JWTs minted by mint_tokens.py; must match on both sides.
    jwt_secret: str
    jwt_algorithm: str = "HS256"

    # Local sentence-transformers model used to embed both docs (ingestion) and queries (chat).
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    # Local, on-disk Chroma persistence path and collection name.
    chroma_path: str = "./chroma_data"
    chroma_collection: str = "policy_docs"

    llm_provider: str = "gemini"  # "gemini" or "openai" — see core/dependencies.get_llm_provider

    # Only the credentials for the active llm_provider need to be set.
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"

    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"


@lru_cache
def get_settings() -> Settings:
    """Returns the process-wide Settings instance, parsing .env only once
    (lru_cache with no args memoizes a single call) and reusing it everywhere else."""
    return Settings()
