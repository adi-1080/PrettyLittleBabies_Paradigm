"""
agents/strategist.py — Agent 2: The Strategist

Compares behavioral fingerprints against the current date to calculate
"Relationship Decay" scores. Uses initiation rate, emoji density, and
response patterns for context-aware decisions — not just silence duration.
"""

import json
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage

from config import llm
from state import AgentState, RelationshipDecay


# ── System Prompt ──────────────────────────────────────────────────────────
STRATEGIST_SYSTEM_PROMPT = """You are **The Strategist** — an expert in relationship-health analytics
who goes far beyond simple "days since last message" calculations.

You will receive:
1. Behavioral Fingerprints (ParticipantProfiles) from the Research Agent.
2. The last-message timestamps per participant.
3. Today's date.

For EACH participant, calculate a **Relationship Decay** score using BOTH
time-based AND behavioral signals:

**Time-based factors (baseline):**
- Days since last message: +10 per day beyond 7 days of silence.

**Behavioral deviation factors (what makes you special):**
- If the contact usually initiates (initiation_rate > 0.5) but hasn't
  messaged in a while → they might be waiting for YOU. Increase priority.
- If your last message was unusually short or lacked emojis compared to
  your usual typing_style → you may be "accidentally ghosting". Note this.
- If the contact is a "Batch Replier" and hasn't sent a batch recently
  → they're likely busy, not disengaged. Reduce score slightly.
- Factor in sentiment_tone: a "Brief & curt" person going silent is less
  alarming than an "Enthusiastic" person going quiet.

Return a JSON **array** of objects with these keys:

- "contact_name"  : (str)  the participant's name
- "decay_score"   : (int)  0–100.  0 = strong bond, 100 = ghosted.
- "risk_factor"   : (str)  detailed human-readable reason referencing
                    SPECIFIC behavioral traits, e.g. "Aakarshit usually
                    initiates 63% of conversations and uses emojis heavily,
                    but you haven't replied in 5 days — possible accidental ghosting."
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

    # Build a lookup of the most recent message timestamp per participant
    last_seen: dict[str, datetime] = {}
    for msg in messages:
        ts = msg.timestamp
        if msg.sender_name not in last_seen or ts > last_seen[msg.sender_name]:
            last_seen[msg.sender_name] = ts

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
            f"Behavioral Fingerprints:\n{profiles_json}\n\n"
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
        print(f"   {flag} {a.contact_name} — score {a.decay_score}/100")
        print(f"      Reason: {a.risk_factor}")

    return {"alerts": alerts}
