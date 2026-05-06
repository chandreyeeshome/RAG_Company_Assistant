from db.mongo import documents_collection
from utils.chunking import chunk_text
from ai.models import embd_model
from vector.qdrant_store import add_chunks

def ingest_content(title, content, category):
    mongo_result = documents_collection.insert_one({
        "title": title,
        "content": content,
        "category": category
    })

    mongo_id = mongo_result.inserted_id

    chunks = chunk_text(
        text = content,
        target_words = 220,
        overlap_words = 40,
        title_prefix = title
    )

    embedding = embd_model.encode(chunks)

    total = add_chunks(
        chunks = chunks,
        embeddings = embedding,
        mongo_id = mongo_id,
        title = title,
        category = category
    )

    return{
        "mongo_id": str(mongo_id),
        "chunks_created": len(chunks),
        "vectors_inserted": total
    }