from vector.qdrant_store import search_chunks
from ai.models import embed, llm
from db.mongo import chat_sessions_collection
import json


def generate_answer(question, contexts):
    context_text = "\n\n".join(contexts)

    prompt = f"""
    You are a helpful and professional company knowledge assistant.

    You must answer using ONLY the information present in the provided context below.

    The provided context may contain TWO types of information:

    --------------------------------------------------
    1. CONVERSATION HISTORY
    --------------------------------------------------
    Previous chat messages between the user and assistant.

    Use this when the user asks things like:
    - what did I ask earlier?
    - what did you say before?
    - repeat the last answer
    - summarize our conversation
    - what was my first question?
    - follow-up questions using words like:
    it, that, earlier, previous, above

    --------------------------------------------------
    2. COMPANY DOCUMENT INFORMATION
    --------------------------------------------------
    Retrieved internal company knowledge such as:
    - WFH policy
    - Leave policy
    - Travel reimbursement
    - Code of conduct
    - IT assets
    - Appraisal
    - HR rules
    etc.

    Use this when the user asks factual company questions.

    --------------------------------------------------
    RULES
    --------------------------------------------------

    1. If user greets you, greet politely in the same language.

    2. If the user asks about earlier chat, previous messages, or memory:
    Use CONVERSATION HISTORY first.

    3. If the user asks policy/company questions:
    Use COMPANY DOCUMENT INFORMATION first.

    4. If both are useful:
    Use both naturally.

    5. If only some part of question is answerable:
    Answer only the answerable part clearly.

    6. If question is unclear:
    Ask for clarification.

    7. If the question is a follow-up scenario based on previous context:
    Apply the policy logically.

    Examples:
    - "I submitted after 10 days"
    - "Can I take 5 WFH days?"
    - "So can I take 22 leaves?"

    Do NOT repeat policy blindly.
    Explain result clearly based on policy.

    8. If exact result is not explicitly stated in context:
    Use careful wording such as:
    - may not be allowed
    - may require approval
    - depends on manager/HR approval

    9. Keep answers concise, clear, professional, and natural.

    10. Never invent policy details not present in context.

    11. If no relevant answer exists in the context:
    Return:

    {{
        "found": false,
        "answer": "I could not find relevant information in the provided documents or conversation history."
    }}

    12. Return ONLY valid JSON.
    Do NOT return markdown.
    Do NOT use ```json blocks.
    Do NOT add explanation outside JSON.

    --------------------------------------------------
    RESPONSE FORMAT
    --------------------------------------------------

    If answer found:

    {{
        "found": true,
        "answer": "your answer"
    }}

    If not found:

    {{
        "found": false,
        "answer": "I could not find relevant information in the provided documents or conversation history."
    }}

    --------------------------------------------------
    CONTEXT
    --------------------------------------------------
    {context_text}

    --------------------------------------------------
    CURRENT USER QUESTION
    --------------------------------------------------
    {question}
    """

    response = llm.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    raw_text = response.text.strip()
    raw_text = raw_text.replace("```json", "").replace("```", "").strip()

    try:
        answer = json.loads(raw_text)
        return answer
    except:
        return {
            "found": False,
            "answer": "Error understanding model response."
        } 



def select_sources(question, filtered_hits):
    q = question.lower()

    memory_words = [
        "earlier", "previous", "summary",
        "summarize", "what did i ask",
        "history", "before"
    ]

    # Conversation history
    for word in memory_words:
        if word in q:
            return ["Conversation History"]
    
    # NO relevant data stored, i.e., NO matches
    if not filtered_hits:
        return []

    # Single match
    if len(filtered_hits) == 1:
        return [filtered_hits[0].payload["title"]]

    # Regular case, multiple matches
    top_score = filtered_hits[0].score

    final_sources = []

    for hit in filtered_hits:
        title = hit.payload["title"]
        
        if hit.score >= top_score - 0.03:
            if title not in final_sources:  # there can be multiple chunks from single document, source will be single
                final_sources.append(title)
     
    # Fallback, atleast show the top scored source, in case of unusual scoring
    if not final_sources:
        final_sources.append(filtered_hits[0].payload["title"])

    return final_sources




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

    for hit in filtered_hits:
        payload = hit.payload

        contexts.append(payload["text"])
    
    full_context = previous_context + "\n\n" + "\n".join(contexts)
    
    answer = generate_answer(question, [full_context])

    if answer["found"] == False:
        return{
            "answer": answer["answer"],
            "sources": []
        }
    final_unique_sources = select_sources(question, filtered_hits)

    return{
        "answer": answer["answer"],
        "sources": final_unique_sources
    }