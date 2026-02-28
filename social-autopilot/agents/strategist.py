"""
agents/strategist.py — Agent 2: The Strategist

Compares relational profiles against the current date to calculate
"Relationship Decay" scores.  Core logic: if the last message from a
contact is older than 7 days, the decay score increases proportionally.
"""

import json
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage

from config import llm
from state import AgentState, RelationshipDecay


# ── System Prompt ──────────────────────────────────────────────────────────
STRATEGIST_SYSTEM_PROMPT = """You are **The Strategist** — an expert in relationship-health analytics.

You will receive:
1. A set of relational profiles (JSON) produced by the Historian.
2. The last-message timestamps per contact.
3. Today's date.

For EACH contact, calculate a **Relationship Decay** score and return a JSON
**array** of objects with these keys:

- "contact_name"  : (str)  the contact's name
- "decay_score"   : (int)  0–100.  0 = strong bond, 100 = ghosted.
                    Base rule: +10 per day of silence beyond 7 days.
                    Also factor in sentiment and frequency from the profile.
- "risk_factor"   : (str)  human-readable reason for the score.
- "is_priority"   : (bool) true if decay_score >= 60.

Return ONLY the JSON array — no markdown fences, no explanation.
"""


def strategist_node(state: AgentState) -> dict:
    """
    LangGraph node that invokes the Strategist agent.

    Reads   : state["messages"], state["profiles"]
    Writes  : {"alerts": List[RelationshipDecay]}
    """
    messages = state["messages"]
    profiles = state["profiles"]

    now = datetime.now(timezone.utc)

    # Build a lookup of the most recent message timestamp per contact
    last_seen: dict[str, datetime] = {}
    for msg in messages:
        ts = msg.timestamp
        if msg.sender not in last_seen or ts > last_seen[msg.sender]:
            last_seen[msg.sender] = ts

    # Prepare context for the LLM
    profiles_json = json.dumps(
        [p.model_dump() for p in profiles], indent=2, default=str
    )
    last_seen_json = json.dumps(
        {name: ts.isoformat() for name, ts in last_seen.items()}, indent=2
    )

    response = llm.invoke([
        SystemMessage(content=STRATEGIST_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Today's date: {now.isoformat()}\n\n"
            f"Relational Profiles:\n{profiles_json}\n\n"
            f"Last-message timestamps:\n{last_seen_json}"
        )),
    ])

    # Parse response
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    alerts_data = json.loads(raw)
    alerts = [RelationshipDecay(**a) for a in alerts_data]

    print(f"\n📊  Strategist produced {len(alerts)} decay alert(s).")
    for a in alerts:
        flag = "🚨" if a.is_priority else "✅"
        print(f"   {flag} {a.contact_name} — score {a.decay_score}/100 "
              f"({a.risk_factor})")

    return {"alerts": alerts}
