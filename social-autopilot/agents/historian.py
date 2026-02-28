"""
agents/historian.py — Agent 1: The Historian

Analyses raw chat logs and extracts structured relational profiles
for each contact. Identifies interaction patterns, shared interests,
response cadence, and overall sentiment.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage

from config import llm
from state import AgentState, RelationalProfile


# ── System Prompt ──────────────────────────────────────────────────────────
HISTORIAN_SYSTEM_PROMPT = """You are **The Historian** — a world-class relationship analyst.

Your mission is to examine raw chat messages and distil them into structured
relational profiles.  For EACH unique contact you find in the messages,
produce one JSON object with the following keys:

- "contact_name"          : (str)  the contact's name
- "interaction_frequency" : (str)  one of "Daily", "Weekly", "Sporadic"
- "average_response_time" : (float) estimated average reply gap in hours
- "top_topics"            : (list[str]) up to 5 recurring conversation themes
- "sentiment_score"       : (float) overall sentiment from -1.0 to 1.0

Return a JSON **array** of these objects — nothing else.
Do NOT wrap the JSON in markdown code fences.
"""


def historian_node(state: AgentState) -> dict:
    """
    LangGraph node that invokes the Historian agent.

    Reads   : state["messages"]  (List[ChatMessage])
    Writes  : {"profiles": List[RelationalProfile]}
    """
    messages = state["messages"]

    # Serialise chat messages into a human-readable block for the LLM
    chat_block = "\n".join(
        f"[{msg.timestamp.isoformat()}] {msg.sender}: {msg.content}"
        for msg in messages
    )

    response = llm.invoke([
        SystemMessage(content=HISTORIAN_SYSTEM_PROMPT),
        HumanMessage(content=f"Here are the chat logs to analyse:\n\n{chat_block}"),
    ])

    # Parse the LLM's JSON response into Pydantic models
    raw = response.content.strip()
    # Strip potential markdown fences the model might add despite instructions
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    profiles_data = json.loads(raw)
    profiles = [RelationalProfile(**p) for p in profiles_data]

    print(f"\n🏛️  Historian identified {len(profiles)} contact profile(s).")
    for p in profiles:
        print(f"   • {p.contact_name} — {p.interaction_frequency}, "
              f"sentiment {p.sentiment_score:+.2f}")

    return {"profiles": profiles}
