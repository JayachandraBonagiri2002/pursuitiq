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
# GPT-5.5: Maximum intelligence, 1M context, configurable reasoning depth
MODEL = os.getenv("MODEL", "gpt-5.5")

# Reasoning effort levels — control how deeply the model thinks per agent
# "high"   = deep multi-step reasoning (for legal analysis, pricing math)
# "medium" = balanced quality + speed (for synthesis, web research)
# "low"    = fast responses (for simple extraction, classification)
REASONING_HIGH = "high"
REASONING_MEDIUM = "medium"
REASONING_LOW = "low"

# ── Vector Store ──────────────────────────────────────────────────────────────
VECTOR_STORE_ID = os.getenv("VECTOR_STORE_ID", "")