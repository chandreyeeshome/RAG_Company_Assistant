from db.mongo import documents_collection
from utils.chunking import chunk_text
from ai.models import embed
from vector.qdrant_store import add_chunks

def ingest_content(title, content, category):

    existing_document = documents_collection.find_one({
        "title": title
    })

    if existing_document:
        return {
            "success": False,
            "message": "Document with the same title already exists."
        }

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

    embeddings = embed(chunks)

    total = add_chunks(
        chunks = chunks,
        embeddings = embeddings,
        mongo_id = mongo_id,
        title = title,
        category = category
    )

    return{
        "success": True,
        "mongo_id": str(mongo_id),
        "chunks_created": len(chunks),
        "vectors_inserted": total
    }