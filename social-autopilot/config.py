"""
config.py — LLM Initialization

Loads the Groq API key from a .env file and initializes the
ChatGroq model (llama-3.3-70b-versatile) for use across agents.
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

# Load environment variables from .env
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError(
        "GROQ_API_KEY not found. "
        "Please set it in your .env file."
    )

# Singleton LLM instance — Groq (LLaMA 3.3 70B)
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.7,
)
