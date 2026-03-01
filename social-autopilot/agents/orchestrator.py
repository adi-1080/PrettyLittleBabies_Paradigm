"""
agents/orchestrator.py — Agent 3: The Social Orchestrator

Generates personalised actions using the owner's Digital Twin as
the persona template. Three modes: Reaction, Nudge, Deep Reply.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage

from config import llm
from save_collection import save_collection
from state import AgentState, ProposedAction, ProposedActionList


ORCHESTRATOR_SYSTEM_PROMPT = """You are **The Social Orchestrator** — a warm, witty social coach
who generates actions that sound EXACTLY like the owner would naturally act.

You receive:
1. The Owner's Behavioral DNA (their Digital Twin — typing style, tone, jargon, emoji habits).
2. Contact DNA profiles with their behavioral traits and anomalies.
3. Strategy Verdicts with recommended actions per contact.
4. **Recent messages** — the last few messages in the conversation so you can understand
   WHO said what, WHO is asking a question, and WHO owes a reply.

For EACH verdict, generate a **Proposed Action**:

**Action Modes:**

1. **Reaction** (recommended_action = "Reaction"):
   - Suggest a SPECIFIC emoji reaction to a specific message.
   - Example: "React with 🔥 to the last Blender render"
   - Keep quick_copy as just the emoji.

2. **Nudge** (recommended_action = "Nudge"):
   - Keep it under 15 words.
   - Reference a core_topic / value anchor from the contact's DNA.
   - Match the owner's typing style (slang, emoji density, formality).

3. **Deep_Reply** (recommended_action = "Deep_Reply"):
   - Draft a full message that continues the conversation naturally.
   - Match the owner's tone and habits exactly — if they use minimal
     punctuation, use minimal punctuation. If they use slang, use slang.
   - Reference shared interests from core_topics.

**CRITICAL CONSTRAINTS:**
- READ THE RECENT MESSAGES CAREFULLY. The owner is identified as sender_id="u1".
- If the OWNER asked a question and is WAITING for the contact's reply,
  do NOT generate a reply as if the owner has the answer. Instead generate
  a gentle follow-up nudge like "any update on X?" or a relevant emoji reaction.
- Only generate a Deep_Reply if the CONTACT asked a question or made a statement
  that the owner should respond to.
- The output must NOT sound like an AI assistant. No "I hope this finds you well."
- If the owner uses slang → use slang. If casual → be casual.
- Prioritise contacts with higher priority scores.
- Keep nudges under 15 words; deep replies under 280 characters when possible.

Return a ProposedActionList containing one action per verdict.
"""


RECENT_MSG_COUNT = 20  # last N messages per contact for context


def build_conversation_state(messages, verdicts):
    """For each contact in verdicts, analyze who sent the last message
    and whether the owner is waiting for a reply."""
    states = []
    for v in verdicts:
        contact_name = v.contact_name
        # Find messages involving this contact
        contact_msgs = [
            m for m in messages
            if m.sender_name == contact_name or m.sender_id == "u1"
        ]
        # Get last few messages
        recent = contact_msgs[-RECENT_MSG_COUNT:]
        if not recent:
            states.append(f"## {contact_name}\nNo recent messages found.\n")
            continue

        last_msg = recent[-1]
        last_sender_is_owner = last_msg.sender_id == "u1"

        # Check if last message looks like a question
        last_content = last_msg.content.strip()
        is_question = last_content.endswith("?") or any(
            w in last_content.lower()
            for w in ["when", "what", "how", "where", "why", "kab", "kya", "kaise"]
        )

        msgs_text = "\n".join(
            f"  {'[OWNER]' if m.sender_id == 'u1' else '[CONTACT]'} {m.sender_name}: {m.content}"
            for m in recent
        )

        # Build explicit state
        if last_sender_is_owner and is_question:
            direction = (
                f"⚠️ CONVERSATION STATE: The OWNER (Anupam) asked a QUESTION and is WAITING "
                f"for {contact_name}'s reply. DO NOT answer this question. "
                f"Generate a follow-up nudge like 'any update?' or an emoji reaction instead."
            )
        elif last_sender_is_owner:
            direction = (
                f"CONVERSATION STATE: The OWNER sent the last message (a statement). "
                f"{contact_name} has not replied yet. Consider a gentle nudge or just wait."
            )
        else:
            direction = (
                f"CONVERSATION STATE: {contact_name} sent the last message. "
                f"The OWNER may owe a reply."
            )

        states.append(f"## {contact_name}\n{direction}\n\nRecent messages:\n{msgs_text}\n")

    return "\n".join(states)


def orchestrator_node(state: AgentState) -> dict:
    owner_profile = state.get("owner_profile")
    profiles = state["profiles"]
    verdicts = state["verdicts"]
    messages = state.get("messages", [])

    owner_json = json.dumps(
        owner_profile.model_dump() if owner_profile else {},
        indent=2, default=str,
    )
    profiles_json = json.dumps([p.model_dump() for p in profiles], indent=2, default=str)
    verdicts_json = json.dumps([v.model_dump() for v in verdicts], indent=2, default=str)

    # Build per-contact conversation state with explicit direction analysis
    conversation_state = build_conversation_state(messages, verdicts)

    structured_llm = llm.with_structured_output(ProposedActionList)

    result = structured_llm.invoke([
        SystemMessage(content=ORCHESTRATOR_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Owner's Digital Twin DNA:\n{owner_json}\n\n"
            f"Contact DNA Profiles:\n{profiles_json}\n\n"
            f"Strategy Verdicts:\n{verdicts_json}\n\n"
            f"Conversation States Per Contact:\n{conversation_state}"
        )),
    ])

    actions = result.actions

    print(f"\n🤖  Orchestrator: {len(actions)} proposed action(s):")
    for a in actions:
        icon = {"Reaction": "👍", "Nudge": "💬", "Deep_Reply": "📝"}.get(a.action_type, "⚪")
        print(f"   {icon} [{a.action_type}] → {a.contact_name}")
        print(f"      Copy: {a.quick_copy}")
        print(f"      Why : {a.rationale}\n")

    save_collection("orchestrator_actions", actions)
    return {"actions": actions}

