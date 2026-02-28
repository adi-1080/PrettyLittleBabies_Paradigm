"""
main.py — Entry Point for Social Life on Auto-Pilot

Initialises the LangGraph pipeline with synthetic chat data
and prints the final auto-pilot recommendations.
"""

from datetime import datetime, timedelta, timezone

from state import ChatMessage
from graph import app


def create_sample_chat_log() -> list[ChatMessage]:
    """
    Generates a realistic synthetic chat log with three contacts
    exhibiting different recency patterns.

    Returns:
        A list of ChatMessage objects.
    """
    now = datetime.now(timezone.utc)

    return [
        # ── Aarav — last messaged 2 days ago (healthy) ─────────────────
        ChatMessage(
            sender="Aarav",
            content="Bro did you watch the F1 qualifying? Verstappen was insane!",
            timestamp=now - timedelta(days=2, hours=5),
        ),
        ChatMessage(
            sender="You",
            content="Yeah! That last lap was unreal. Monaco is going to be epic.",
            timestamp=now - timedelta(days=2, hours=4),
        ),
        ChatMessage(
            sender="Aarav",
            content="We should do a watch party for the race. I'll bring pizza 🍕",
            timestamp=now - timedelta(days=2, hours=3),
        ),
        ChatMessage(
            sender="You",
            content="I'm in! Let's plan it this weekend.",
            timestamp=now - timedelta(days=2, hours=2),
        ),

        # ── Priya — last messaged 12 days ago (decaying) ──────────────
        ChatMessage(
            sender="Priya",
            content="Hey! I just got the offer from Google! 🎉",
            timestamp=now - timedelta(days=12),
        ),
        ChatMessage(
            sender="You",
            content="WHAT! That's amazing, congrats!! We need to celebrate!",
            timestamp=now - timedelta(days=12, hours=-1),
        ),
        ChatMessage(
            sender="Priya",
            content="Thanks! Let's plan something soon. Also, any recs for Bangalore?",
            timestamp=now - timedelta(days=11),
        ),

        # ── Dev — last messaged 25 days ago (critical) ────────────────
        ChatMessage(
            sender="Dev",
            content="Yo, you still into that Node.js side project?",
            timestamp=now - timedelta(days=25),
        ),
        ChatMessage(
            sender="You",
            content="Yeah man, been stuck on the auth module. Wanna pair on it?",
            timestamp=now - timedelta(days=25, hours=-2),
        ),
        ChatMessage(
            sender="Dev",
            content="Sure, I'll look at it this weekend and get back to you.",
            timestamp=now - timedelta(days=24),
        ),
    ]


def main():
    """Run the Social Autopilot pipeline end-to-end."""
    print("=" * 60)
    print("  🚀  SOCIAL LIFE ON AUTO-PILOT  🚀")
    print("=" * 60)

    sample_messages = create_sample_chat_log()

    print(f"\n📨  Loaded {len(sample_messages)} synthetic messages "
          f"across {len({m.sender for m in sample_messages})} contacts.\n")

    # Invoke the LangGraph pipeline
    initial_state = {
        "messages": sample_messages,
        "profiles": [],
        "alerts": [],
        "final_recommendations": [],
    }

    result = app.invoke(initial_state)

    # ── Final summary ─────────────────────────────────────────────────
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
