"""
agents/orchestrator.py — Agent 3: The Orchestrator

Generates personalised "social nudges" — ready-to-send message drafts
that match each contact's communication style, using behavioral
fingerprints for tone-perfect message crafting.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage

from config import llm
from state import AgentState, SocialNudge


# ── System Prompt ──────────────────────────────────────────────────────────
ORCHESTRATOR_SYSTEM_PROMPT = """You are **The Orchestrator** — a warm, witty social coach who writes
messages that sound EXACTLY like the user would naturally write.

You will receive:
1. Behavioral Fingerprints for each participant (typing style, emoji
   usage, formality, topics, sentiment).
2. Decay alerts showing which relationships need attention and why.

For EACH alert, craft a personalised **Social Nudge** and return a JSON
**array** of objects with these keys:

- "contact_name"    : (str)  who to message.
- "nudge_type"      : (str)  one of "Follow-up", "Check-in", "Meme-share",
                              "Deep-catch-up", or "Congratulate".
- "generated_draft" : (str)  the actual message text — it MUST match the
                              user's typical typing style:
                              * If they use slang → use slang.
                              * If they use emojis → include emojis.
                              * If they're formal → keep it formal.
                              * Reference shared topics from the profile.
- "rationale"       : (str)  brief explanation referencing specific
                              behavioral traits that informed this nudge.

Guidelines:
- The draft should feel like the user writing, not a robot.
- Reference specific shared interests from top_topics.
- If the contact has high initiation_rate, acknowledge their effort.
- Keep messages under 280 characters when possible.
- Prioritise contacts with higher decay scores.

Return ONLY the JSON array — no markdown fences, no extra text.
"""


def orchestrator_node(state: AgentState) -> dict:
    """
    LangGraph node that invokes the Orchestrator agent.

    Reads   : state["profiles"], state["alerts"]
    Writes  : {"final_recommendations": List[SocialNudge]}
    """
    profiles = state["profiles"]
    alerts = state["alerts"]

    profiles_json = json.dumps(
        [p.model_dump() for p in profiles], indent=2, default=str
    )
    alerts_json = json.dumps(
        [a.model_dump() for a in alerts], indent=2, default=str
    )

    response = llm.invoke([
        SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Behavioral Fingerprints:\n{profiles_json}\n\n"
            f"Decay Alerts:\n{alerts_json}"
        )),
    ])

    # Parse response
    raw = response.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    raw = raw.strip()

    nudges_data = json.loads(raw)
    nudges = [SocialNudge(**n) for n in nudges_data]

    print(f"\n🤖  Orchestrator generated {len(nudges)} nudge(s).")
    for n in nudges:
        print(f"   💬 [{n.nudge_type}] → {n.contact_name}")
        print(f"      Draft : {n.generated_draft}")
        print(f"      Why   : {n.rationale}\n")

    return {"final_recommendations": nudges}
