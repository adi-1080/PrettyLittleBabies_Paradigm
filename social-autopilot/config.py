"""
config.py — LLM Initialization

Initializes the Ollama model (gpt-oss:20b) for use across agents.
"""

import os
from dotenv import load_dotenv
from langchain_ollama import ChatOllama

# Load environment variables (optional for Ollama but habit-forming)
load_dotenv()

# Singleton LLM instance — Ollama (gpt-oss-20b)
llm = ChatOllama(
    model="gpt-oss:20b",
    temperature=0.7,
)

