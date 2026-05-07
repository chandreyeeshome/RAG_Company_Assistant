import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PayloadSchemaType
)

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

print("Qdrant connected successfully!")

COLLECTION_NAME = "rag_docs"

collections = client.get_collections().collections
existing_collections = [c.name for c in collections]


if COLLECTION_NAME not in existing_collections:

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=3072,
            distance=Distance.COSINE
        )
    )

    print("New collection created.")


    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="mongo_id",
        field_schema=PayloadSchemaType.KEYWORD
    )

    print("mongo_id payload index created.")

else:
    print("Collection already exists.")