from vector.qdrant_db import client
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue
)

import uuid

COLLECTION_NAME = "rag_docs"


def add_chunks(chunks, embeddings, mongo_id, title, category):

    points = []

    for i, (chunk, vector) in enumerate(zip(chunks, embeddings)):

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "mongo_id": str(mongo_id),
                "chunk_no": i + 1,
                "title": title,
                "text": chunk,
                "category": category
            }
        )

        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return len(points)


def search_chunks(query_embedding, top_k=3):

    try:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_embedding,
            limit=top_k
        )

        return results.points

    except Exception as e:
        print("Qdrant search error:", e)
        return []


def delete_document_chunks(mongo_id):

    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="mongo_id",
                    match=MatchValue(value=str(mongo_id))
                )
            ]
        )
    )

    return True