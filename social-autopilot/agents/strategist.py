"""
agents/strategist.py — Agent 2: The Social Strategist

Value Mapping: compares current conversation window against the
Historian's baseline DNA to classify each relationship as
Active / Stagnant / Debt and recommend Reaction / Nudge / Deep_Reply.
"""

import json
from datetime import datetime, timezone

from langchain_core.messages import SystemMessage, HumanMessage

from config import llm
from save_collection import save_collection, load_collection
from state import AgentState, StrategyVerdict, StrategyVerdictList, FeedbackEntry


STRATEGIST_SYSTEM_PROMPT = """You are **The Social Strategist** — an expert in relationship-health
analytics who goes far beyond "days since last message."

You receive:
1. Behavioral DNA profiles (from the Historian) for each contact.
2. The "Current Window" — the last 20-30 messages of the conversation.
3. Today's date and last-message timestamps.
4. Past feedback (actions the user previously Rejected — avoid repeating those).

For EACH contact, perform **Value Mapping**:

**Sentiment Drift:**
- Compare the current window's tone against the DNA's vibe_description.
- Is it Warmer, Stable, or Colder?

**Social Debt Detection:**
- Does the user (the owner) owe a reply?
- Deep Debt: a question was asked and not answered.
- Shallow Debt: a meme, link, or statement was sent with no response.

**Urgency Assessment:**
- Factor in the contact's comm_style (Batcher vs Streamer).
- A Batcher going quiet is less alarming than a Streamer going silent.
- Factor in reciprocity_ratio: if they usually initiate but haven't → they may be waiting.

**Decision Rules:**
- IF conversation is active AND vibe is good → recommended_action: "Reaction"
- IF conversation stalled > 3 days AND last message was a statement → "Nudge"
- IF a question was asked > 24 hours ago with no reply → "Deep_Reply"
- IF the contact is a Batcher and hasn't sent a batch recently → reduce priority (less alarming)

**Anomaly Awareness:**
- If the DNA includes anomalies (e.g. latency spike, emoji drop), reference them.

Return a StrategyVerdictList containing one verdict per contact, sorted by priority (highest first).
"""


def strategist_node(state: AgentState) -> dict:
    profiles = state["profiles"]
    messages = state["messages"]

    now = datetime.now(timezone.utc)

    window = messages[-30:]
    window_text = "\n".join(
        f"[{m.timestamp.isoformat()}] {m.sender_name}: {m.content}"
        for m in window if m.content.strip()
    )

    last_seen: dict[str, datetime] = {}
    for msg in messages:
        if msg.sender_name not in last_seen or msg.timestamp > last_seen[msg.sender_name]:
            last_seen[msg.sender_name] = msg.timestamp

    feedback_history = load_collection("feedback", FeedbackEntry)
    rejected = [
        f"{f.contact_name}: {f.action_type}" for f in feedback_history if f.decision == "Rejected"
    ]

    profiles_json = json.dumps([p.model_dump() for p in profiles], indent=2, default=str)
    last_seen_json = json.dumps({n: ts.isoformat() for n, ts in last_seen.items()}, indent=2)

    feedback_context = ""
    if rejected:
        feedback_context = f"\n\nPreviously REJECTED actions (do NOT repeat these):\n" + "\n".join(f"- {r}" for r in rejected)

    structured_llm = llm.with_structured_output(StrategyVerdictList)

    result = structured_llm.invoke([
        SystemMessage(content=STRATEGIST_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Today's date: {now.isoformat()}\n\n"
            f"Behavioral DNA Profiles:\n{profiles_json}\n\n"
            f"Current Window (last {len(window)} messages):\n{window_text}\n\n"
            f"Last-message timestamps:\n{last_seen_json}"
            f"{feedback_context}"
        )),
    ])

    verdicts = result.verdicts
    verdicts.sort(key=lambda v: v.priority, reverse=True)

    print(f"\n📊  Strategist: {len(verdicts)} verdict(s), priority-sorted:")
    for v in verdicts:
        icon = {"Reaction": "💚", "Nudge": "💛", "Deep_Reply": "🔴"}.get(v.recommended_action, "⚪")
        print(f"   {icon} {v.contact_name} — P{v.priority} [{v.state}] → {v.recommended_action}")
        print(f"      Drift: {v.sentiment_drift} | Debt: {v.debt_type}")
        print(f"      Reason: {v.reasoning}")
        if v.anomalies:
            for a in v.anomalies:
                print(f"      ⚠️  {a}")

    save_collection("strategist_verdicts", verdicts)
    return {"verdicts": verdicts}

