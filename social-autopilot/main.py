"""
main.py — Entry Point for Social Life on Auto-Pilot

Loads real WhatsApp JSON chat data, feeds it through the LangGraph
pipeline, and prints behavioral fingerprints + auto-pilot recommendations.
"""

import json
import os
from pathlib import Path

from state import MessageModel
from graph import app


# Path to the real chat data JSON
CHAT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "chat_data.json"

# Maximum messages to send through the pipeline (context window limit)
MAX_MESSAGES = 200


def load_chat_data(path: Path, max_messages: int = MAX_MESSAGES) -> list[MessageModel]:
    """
    Load and parse the WhatsApp JSON export into MessageModel objects.
    Samples the most recent `max_messages` to stay within LLM context limits.

    Args:
        path: Path to the chat_data.json file.
        max_messages: Maximum number of messages to process.

    Returns:
        A list of MessageModel objects.
    """
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_messages = data.get("messages", [])

    # Take the most recent messages for context
    sampled = raw_messages[-max_messages:]

    messages = [MessageModel(**m) for m in sampled]

    print(f"📂  Loaded {len(raw_messages)} total messages from: {path.name}")
    print(f"📨  Using most recent {len(messages)} messages for analysis.")

    # Show participant info
    participants = data.get("participants", [])
    if participants:
        names = ", ".join(p["name"] for p in participants)
        print(f"👥  Participants: {names}")

    return messages


def main():
    """Run the Social Autopilot pipeline end-to-end with real chat data."""
    print("=" * 60)
    print("  🚀  SOCIAL LIFE ON AUTO-PILOT  🚀")
    print("  🧬  Behavioral Fingerprinting Edition")
    print("=" * 60)

    if not CHAT_DATA_PATH.exists():
        print(f"\n❌  Chat data not found at: {CHAT_DATA_PATH}")
        print("   Place your exported chat JSON at that path and try again.")
        return

    messages = load_chat_data(CHAT_DATA_PATH)

    unique_senders = {m.sender_name for m in messages}
    print(f"\n🔬  Analyzing {len(unique_senders)} unique participants...\n")

    # Invoke the LangGraph pipeline
    initial_state = {
        "messages": messages,
        "profiles": [],
        "alerts": [],
        "final_recommendations": [],
    }

    result = app.invoke(initial_state)

    # ── Behavioral Fingerprints ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("  🧬  BEHAVIORAL FINGERPRINTS")
    print("=" * 60)

    for p in result["profiles"]:
        print(f"\n  📋 {p.sender_name} ({p.sender_id})")
        print(f"     Tone        : {p.sentiment_tone}")
        print(f"     Formality   : {p.typing_style.formality_level}")
        print(f"     Slang       : {'✅ Yes' if p.typing_style.use_of_slang else '❌ No'}")
        print(f"     Emoji/msg   : {p.typing_style.emoji_density:.2f}")
        print(f"     Avg words   : {p.typing_style.avg_word_count}")
        print(f"     Punctuation : {p.typing_style.punctuation_style}")
        print(f"     Jargon      : {', '.join(p.typing_style.jargon_used) or 'None'}")
        print(f"     Latency     : {p.communication_patterns.reply_latency_seconds:.0f}s")
        print(f"     Response    : {p.communication_patterns.responsiveness}")
        print(f"     Init rate   : {p.communication_patterns.initiation_rate:.1%}")
        print(f"     Peak hours  : {p.communication_patterns.peak_activity_hours}")
        print(f"     Batch msg   : {'✅ Yes' if p.communication_patterns.batch_messaging else '❌ No'}")
        print(f"     Topics      : {', '.join(p.top_topics)}")

    # ── Final recommendations ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  📋  FINAL AUTO-PILOT RECOMMENDATIONS")
    print("=" * 60)

    for i, nudge in enumerate(result["final_recommendations"], 1):
        print(f"\n  {i}. [{nudge.nudge_type}] → {nudge.contact_name}")
        print(f"     Message : {nudge.generated_draft}")
        print(f"     Reason  : {nudge.rationale}")

    if not result["final_recommendations"]:
        print("\n  ✅  All relationships are healthy — no nudges needed!")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
