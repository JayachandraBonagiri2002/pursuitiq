"""
config.py — All settings come from here. Never hardcode keys anywhere else.
"""
import os
from dotenv import load_dotenv

load_dotenv()  # Reads your .env file

# ── OpenAI ────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not OPENAI_API_KEY:
    raise EnvironmentError(
        "OPENAI_API_KEY not found. Copy .env.example to .env and add your key."
    )

# ── Models ────────────────────────────────────────────────────────────────────
MODEL = os.getenv("MODEL", "gpt-5.5")
MODEL_LIGHT = os.getenv("MODEL_LIGHT", "gpt-4.1-mini")

REASONING_HIGH = "high"
REASONING_MEDIUM = "medium"
REASONING_LOW = "low"

# ── Pipeline concurrency (reduce if hitting rate limits) ─────────────────────
MAX_PARALLEL_AGENTS = int(os.getenv("MAX_PARALLEL_AGENTS", "4"))

# ── Vector Store (legacy deal corpus) ─────────────────────────────────────────
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "")

# ── Azure Blob Storage (proposal knowledge base) ─────────────────────────────
AZURE_STORAGE_ACCOUNT_URL = os.getenv(
    "AZURE_STORAGE_ACCOUNT_URL",
    "https://stpursuitiq.blob.core.windows.net"
)
AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")

# ── Azure AI Search (semantic search over proposals) ──────────────────────────
AZURE_SEARCH_ENDPOINT = os.getenv(
    "AZURE_SEARCH_ENDPOINT",
    "https://search-pursuitiq.search.windows.net"
)
AZURE_SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY", "")
