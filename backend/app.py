from flask import Flask, request, jsonify
from db.mongo import documents_collection, chat_sessions_collection
from vector.qdrant_store import (
    delete_document_chunks,
    clear_collection
)
from bson import ObjectId
from services.ingest_service import ingest_content
from services.search_service import ask_question
from services.vector_service import build_vectors
from flask_cors import CORS 
import os

app = Flask(__name__)
CORS(app, supports_credentials=True)

@app.route("/")
def home():
    return {"message": "Backend connected to MongoDB successfully!"}



@app.route("/documents", methods=["POST"])
def ingest():
    data = request.get_json()

    title = data.get("title", "").strip()
    content = data.get("content", "").strip()
    category = data.get("category", "").strip()

    if not title or not content or not category:
        return jsonify({
            "error":"Title, Content and Category is required."
        }), 400
    
    result = ingest_content(title, content, category)

    if not result["success"]:
        if result.get("error_code") == "DUPLICATE_DOCUMENT":
            return jsonify({
                "message": result["message"]
            }), 409

        return jsonify({
            "message": result["message"],
            "error": result.get("error", "")
        }), 500

    return jsonify({
        "message": "Ingestion successful.",
        "data": result
    }), 201

@app.route("/documents", methods=["GET"])
def get_documents():

    docs = documents_collection.find()

    result = []

    for doc in docs:
        result.append({
            "_id": str(doc["_id"]),
            "title": doc["title"],
            "category": doc["category"],
            "content": doc["content"]
        })

    return jsonify({"data": result})


@app.route("/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):

    try:
        object_id = ObjectId(doc_id)

    except Exception as e:
        return jsonify({
            "message": "Invalid document id.",
            "error": str(e)
        }), 400

    try:

        result = documents_collection.delete_one({
            "_id": object_id
        })

        if result.deleted_count == 0:
            return jsonify({
                "message": "Document not found in MongoDB."
            }), 404

    except Exception as e:

        return jsonify({
            "message": "Failed to delete document from MongoDB.",
            "error": str(e)
        }), 500

    try:

        delete_document_chunks(doc_id)

        return jsonify({
            "message": "Document deleted successfully."
    }), 200

    except Exception:

        #Retry once in case of a temporary Qdrant/network failure.
        try:

            delete_document_chunks(doc_id)

            return jsonify({
                "message": "Document deleted successfully."
            }), 200

        except Exception as e:

            return jsonify({
                "message": "Document deleted from MongoDB, but failed to delete vectors from Qdrant.",
                "error": str(e)
            }), 500



@app.route("/ask", methods=["POST"])
def ask_query():
    data = request.get_json()

    question = data.get("question", "").strip()

    session_id = data.get("session_id", "").strip()
    if not session_id:
        session_id = "default"


    if not question:
        return jsonify({"error": "Question required."}), 400
    
    result = ask_question(question, session_id)


    chat_sessions_collection.insert_one({
        "session_id": session_id,
        "question": question,
        "answer": result["answer"],
        "sources": result["sources"]
    })

    return jsonify({
        "answer": result.get("answer", ""),
        "sources": result.get("sources", [])
    })



@app.route("/chat-history/<session_id>", methods=["GET"])
def get_chat_history(session_id):

    chats = chat_sessions_collection.find({
        "session_id": session_id
    }).sort("_id", 1)

    result = []

    for chat in chats:
        result.append({
            "question": chat["question"],
            "answer": chat["answer"],
            "sources": chat["sources"]
        })

    return jsonify(result)



@app.route("/chat-history/<session_id>", methods=["DELETE"])
def delete_chat(session_id):

    chat_sessions_collection.delete_many({
        "session_id": session_id
    })

    return jsonify({
        "message": "Chat session deleted"
    })


# Rebuilds the Qdrant vector index from MongoDB documents.
# Used when the free Qdrant cluster is recreated or reset.
@app.route("/admin/rebuild-index", methods=["POST"])
def rebuild_index():

    admin_secret = request.headers.get("x-admin-secret")

    if admin_secret != os.getenv("ADMIN_SECRET"):
        return jsonify({
            "message": "Unauthorized"
        }), 401

    try:

        clear_collection()

        documents = documents_collection.find()

        documents_processed = 0
        chunks_created = 0
        vectors_inserted = 0

        for document in documents:

            result = build_vectors(
                mongo_id=document["_id"],
                title=document["title"],
                content=document["content"],
                category=document["category"]
            )

            documents_processed += 1
            chunks_created += result["chunks_created"]
            vectors_inserted += result["vectors_inserted"]

        return jsonify({
            "message": "Vector index rebuilt successfully.",
            "documents_processed": documents_processed,
            "chunks_created": chunks_created,
            "vectors_inserted": vectors_inserted
        }), 200

    except Exception as e:

        return jsonify({
            "message": "Failed to rebuild vector index.",
            "error": str(e)
        }), 500



if __name__ == "__main__":
    app.run(debug=True)