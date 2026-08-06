from db.mongo import documents_collection
from services.vector_service import build_vectors

def ingest_content(title, content, category):

    mongo_id = None

    try:

        existing_document = documents_collection.find_one({
            "title": title
        })

        if existing_document:
            return {
                "success": False,
                "error_code": "DUPLICATE_DOCUMENT",
                "message": "Document with the same title already exists."
            }

        mongo_result = documents_collection.insert_one({
            "title": title,
            "content": content,
            "category": category
        })

        mongo_id = mongo_result.inserted_id

    
        result = build_vectors(
            mongo_id=mongo_id,
            title=title,
            content=content,
            category=category
        )

        return {
            "success": True,
            "mongo_id": str(mongo_id),
            "chunks_created": result["chunks_created"],
            "vectors_inserted": result["vectors_inserted"]
        }
    
    except Exception as e:

        if mongo_id is not None:
            documents_collection.delete_one({
                "_id" : mongo_id
            })

        return{
            "success" : False,
            "message" : "Document ingestion failed",
            "error" : str(e)
        }