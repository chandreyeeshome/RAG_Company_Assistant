import os

from dotenv import load_dotenv
from google import genai

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file!")
else:
    print("API Key loaded successfully.")
    print("Loaded Key Prefix:", api_key[:12])
    print("Loaded Key Length:", len(api_key))

llm = genai.Client(api_key=api_key)

def embed(texts):
    if isinstance(texts, str):
        texts = [texts]
    
    result = llm.models.embed_content(
        model="gemini-embedding-001",
        contents=texts
    )

    return [e.values for e in result.embeddings]