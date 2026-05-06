from vector.qdrant_store import search_chunks
from ai.models import embed, llm
from db.mongo import chat_sessions_collection
import json


def generate_answer(question, contexts):
    context_text = "\n\n".join(contexts)

    prompt = f"""

    You are a helpful company assistant.
    Answer ONLY from the provided context.

    RULES:
    1. If user greets you, greet them back, in their language.
    2. If the context contains answers for ALL parts of the question, answer the entire question, give clear concise answer.
    3. If the context contains answers for only SOME parts of the question, answer those parts and ignore the rest.
    4. If NO part of the question can be answered, respond with 'I could not find information regarding this in the provided documents.'.
    5. If the question is ambiguous or unclear, ask for clarification.

    Return ONLY valid JSON in this exact format:
    
    {{
        "found": true,
        "answer": "your answer"
    }}

    OR

    {{
        "found": false,
        "answer": "I could not find relevant information in the provided documents."
    }}

    Conversation + Retrieved Context:
    {context_text}

    Question:
    {question}

    """
        
    response = llm.models.generate_content(
        model = "gemini-2.5-flash",
        contents = prompt
    )

    raw_text =  response.text.strip()

    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        answer = json.loads(raw_text)
        return answer   
    except:
        return{
            "found": False,
            "answer": "Error understanding model response."
        } 

def ask_question(question, session_id=None):

    previous_context = ""

    if session_id:
        recent_chats = list(
            chat_sessions_collection.find(
                    {"session_id": session_id}
            ).sort("_id", -1).limit(3)
        )
    
        recent_chats.reverse()

        history = []

        for chat in recent_chats:
            history.append(
                f"User: {chat['question']}\nAssistant: {chat['answer']}"
            )

        previous_context = "\n".join(history)

    query_vector = embed(question)[0]

    hits = search_chunks(query_vector, top_k=3)

    if not hits:
        return{
            "answer": "No relevant documents or information found.",
            "sources": []
        }

    THRESHOLD = 0.50

    filtered_hits = []

    for hit in hits:
        if hit.score >= THRESHOLD:
            filtered_hits.append(hit)
    
    if not filtered_hits:
        return{
            "answer": "No relevant documents or information found.",
            "sources": []
        }

    contexts = []
    sources = []

    for hit in filtered_hits:
        payload = hit.payload

        contexts.append(payload["text"])
        sources.append(payload["title"])
    
    full_context = previous_context + "\n\n" + "\n".join(contexts)
    
    answer = generate_answer(question, [full_context])

    if answer["found"] == False:
        return{
            "answer": answer["answer"],
            "sources": []
        }
    unique_sources = list(dict.fromkeys(sources))

    return{
        "answer": answer["answer"],
        "sources": unique_sources
    }