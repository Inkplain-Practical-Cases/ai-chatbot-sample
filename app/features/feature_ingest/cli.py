# Entry point: `python -m app.features.feature_ingest.cli`
# Walks docs/, extracts text (OCR fallback for scanned pages), chunks it,
# embeds the chunks, and writes them + RBAC metadata into the vector store.
from pathlib import Path

from app.core.config import get_settings
from app.features.feature_ingest.configs.access_map import get_access_entry
from app.features.feature_ingest.services.service_chunk_text import service_chunk_text
from app.features.feature_ingest.services.service_extract_pdf import service_extract_pdf
from app.features.feature_ingest.services.service_ocr_pdf import service_ocr_pdf_page
from app.providers.embeddings.sentence_transformers_provider import SentenceTransformersProvider
from app.providers.vectorstore.base import Chunk
from app.providers.vectorstore.chroma_store import ChromaStore

DOCS_ROOT = Path(__file__).resolve().parents[3] / "docs"


def _build_chunks_for_pdf(pdf_path: Path, relative_path: str) -> list[Chunk]:
    """Extracts every page of `pdf_path`, OCRs any page pypdf couldn't read,
    then splits each page's text into overlapping chunks tagged with the
    RBAC metadata (department/access_level) looked up from ACCESS_MAP."""
    # RBAC metadata is the same for every chunk of this file, so look it up once.
    access = get_access_entry(relative_path)
    pages_text = service_extract_pdf(pdf_path)

    chunks: list[Chunk] = []
    for page_index, page_text in enumerate(pages_text):
        # Empty page from pypdf means it's likely scanned — fall back to OCR
        # automatically, no manual flagging of which files need it.
        text = page_text or service_ocr_pdf_page(pdf_path, page_index)
        if not text:
            continue

        # chunk_index makes each chunk's id unique within the page, so re-running
        # ingestion on the same file overwrites (upserts) rather than duplicates.
        for chunk_index, chunk_text in enumerate(service_chunk_text(text)):
            chunks.append(
                Chunk(
                    id=f"{relative_path}:{page_index}:{chunk_index}",
                    text=chunk_text,
                    department=access.department,
                    access_level=access.access_level,
                    source_file=pdf_path.name,
                    page=page_index + 1,
                )
            )
    return chunks


def main() -> None:
    """Ingestion entry point: discovers every PDF under docs/<department>/,
    turns each one into RBAC-tagged chunks, embeds all of them in a single
    batch, and upserts the result into the configured Chroma collection."""
    settings = get_settings()
    embedder = SentenceTransformersProvider(settings.embedding_model)
    store = ChromaStore(path=settings.chroma_path, collection_name=settings.chroma_collection)

    all_chunks: list[Chunk] = []
    # docs/*/*.pdf: one level of department subfolders under docs/, e.g. docs/hr/leave_policy.pdf.
    for pdf_path in sorted(DOCS_ROOT.glob("*/*.pdf")):
        relative_path = pdf_path.relative_to(DOCS_ROOT).as_posix()
        print(f"Processing {relative_path} ...")
        chunks = _build_chunks_for_pdf(pdf_path, relative_path)
        print(f"  -> {len(chunks)} chunks")
        all_chunks.extend(chunks)

    if not all_chunks:
        print("No chunks produced — nothing to write.")
        return

    # Embedding is batched across every chunk from every file, one model call
    # instead of one per chunk, since the embedding model has fixed per-call overhead.
    print(f"Embedding {len(all_chunks)} chunks with {settings.embedding_model} ...")
    embeddings = embedder.embed([c.text for c in all_chunks])

    print(f"Writing to Chroma collection '{settings.chroma_collection}' at {settings.chroma_path} ...")
    store.upsert(all_chunks, embeddings)

    print("Ingestion complete.")


if __name__ == "__main__":
    main()
