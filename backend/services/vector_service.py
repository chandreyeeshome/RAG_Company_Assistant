from utils.chunking import chunk_text
from ai.models import embed
from vector.qdrant_store import add_chunks


def build_vectors(mongo_id, title, content, category):

    chunks = chunk_text(
        text=content,
        target_words=220,
        overlap_words=40,
        title_prefix=title
    )

    embeddings = embed(chunks)

    total = add_chunks(
        chunks=chunks,
        embeddings=embeddings,
        mongo_id=mongo_id,
        title=title,
        category=category
    )

    return {
        "chunks_created": len(chunks),
        "vectors_inserted": total
    }