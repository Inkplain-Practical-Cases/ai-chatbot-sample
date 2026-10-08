# Concrete VectorStore backed by Chroma's local/persistent client — no
# Docker or external server required, data lives under settings.chroma_path.
import chromadb

from app.providers.vectorstore.base import Chunk


class ChromaStore:
    """Concrete VectorStore backed by a local, persistent Chroma collection."""

    def __init__(self, path: str, collection_name: str) -> None:
        # get_or_create so ingestion can be re-run against the same collection
        # without a manual setup step.
        client = chromadb.PersistentClient(path=path)
        self._collection = client.get_or_create_collection(collection_name)

    def upsert(self, chunks: list[Chunk], embeddings: list[list[float]]) -> None:
        """Writes each chunk's embedding, text, and RBAC/source metadata to
        the collection. `chunks` and `embeddings` must be the same length and
        in matching order. Existing ids are overwritten, not duplicated."""
        self._collection.upsert(
            ids=[c.id for c in chunks],
            embeddings=embeddings,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "department": c.department,
                    "access_level": c.access_level,
                    "source_file": c.source_file,
                    "page": c.page,
                }
                for c in chunks
            ],
        )

    def query(
        self,
        query_embedding: list[float],
        department: str,
        level: int,
        limit: int = 5,
    ) -> list[Chunk]:
        """Runs a similarity search for `query_embedding`, restricted to
        chunks the (department, level) pair may see, and returns up to
        `limit` matches as Chunk objects, most similar first."""
        # RBAC filter enforced at the DB layer: (own department OR hr) AND
        # access_level <= user's level. See A2 doc §8 for the rationale.
        where_filter = {
            "$and": [
                {"$or": [{"department": department}, {"department": "hr"}]},
                {"access_level": {"$lte": level}},
            ]
        }

        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter,
        )

        # Chroma's query API is batched (one query per outer list index); we
        # only ever send a single query embedding, so index [0] unwraps it.
        ids = result["ids"][0]
        documents = result["documents"][0]
        metadatas = result["metadatas"][0]

        return [
            Chunk(
                id=chunk_id,
                text=text,
                department=meta["department"],
                access_level=meta["access_level"],
                source_file=meta["source_file"],
                page=meta["page"],
            )
            for chunk_id, text, meta in zip(ids, documents, metadatas)
        ]
