# Splits one page's extracted text into overlapping word-based chunks.
# Word count (not raw characters) approximates token count closely enough for
# a policy-document RAG use case, without pulling in a tokenizer dependency.
CHUNK_SIZE_WORDS = 300
CHUNK_OVERLAP_WORDS = 50


def service_chunk_text(
    text: str,
    chunk_size: int = CHUNK_SIZE_WORDS,
    overlap: int = CHUNK_OVERLAP_WORDS,
) -> list[str]:
    """Splits `text` into a list of chunks of up to `chunk_size` words each,
    with `overlap` words repeated between consecutive chunks so a sentence
    straddling a chunk boundary still appears whole in at least one chunk."""
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    start = 0
    step = chunk_size - overlap  # how far the window advances each iteration
    while start < len(words):
        chunk_words = words[start : start + chunk_size]
        chunks.append(" ".join(chunk_words))
        if start + chunk_size >= len(words):
            # Last chunk already reaches the end of the text — stop, otherwise
            # the overlap step would produce a trailing near-duplicate chunk.
            break
        start += step

    return chunks
