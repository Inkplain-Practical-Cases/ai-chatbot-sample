# Local, free embedding provider — downloads the model once (~100MB) and
# runs on CPU. This is the concrete EmbeddingProvider used by default.
from sentence_transformers import SentenceTransformer


class SentenceTransformersProvider:
    """Concrete EmbeddingProvider wrapping a local sentence-transformers model."""

    def __init__(self, model_name: str) -> None:
        # Downloads/loads the model weights once at construction time; construction
        # is deliberately memoized behind get_embedder() so this only happens once per process.
        self._model = SentenceTransformer(model_name)

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Encodes a batch of texts into one embedding vector per text, in
        the same order as the input."""
        return self._model.encode(texts, convert_to_numpy=True).tolist()
