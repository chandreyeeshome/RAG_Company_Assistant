from vector.qdrant_db import client
from qdrant_client.models import Distance, VectorParams

client.create_collection(
    collection_name="rag_docs",
    vectors_config=VectorParams(
        size=384,
        distance=Distance.COSINE
    )
)

print("Collection 'rag_docs' created successfully in Qdrant!")