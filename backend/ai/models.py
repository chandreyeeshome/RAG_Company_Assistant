import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

from dotenv import load_dotenv
from google import genai
from sentence_transformers import SentenceTransformer

load_dotenv(override=True)

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file!")
else:
    print("New API Key loaded successfully.")
    print("Loaded Key Prefix:", api_key[:12])
    print("Loaded Key Length:", len(api_key))

embd_model = SentenceTransformer(
    "all-MiniLM-L6-v2",
    device="cpu"
)

llm = genai.Client(api_key=api_key) 