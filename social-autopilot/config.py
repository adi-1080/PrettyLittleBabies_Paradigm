"""
config.py — LLM Initialization

Loads the Google API key from a .env file and initializes the
ChatGoogleGenerativeAI model (Gemini 2.0 Flash) for use across agents.
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment variables from .env
load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError(
        "GOOGLE_API_KEY not found. "
        "Please set it in your .env file."
    )

# Singleton LLM instance — Gemini 2.0 Flash
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7,
)
