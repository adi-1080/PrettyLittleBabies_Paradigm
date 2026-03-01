"""
main.py — Entry Point for Social Life on Auto-Pilot

Scans ALL chat_*.json files in ../data/, runs the 3-agent pipeline
for each, and aggregates results into the collections folder.
"""

import json
from datetime import datetime
from pathlib import Path

from state import MessageModel, FeedbackEntry
from graph import app
from save_collection import load_collection, save_collection


DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MAX_MESSAGES = 200


def discover_chat_files() -> list[Path]:
    """Find all chat_*.json files in the data directory."""
    files = sorted(DATA_DIR.glob("chat_*.json"))
    return files


def load_chat_data(path: Path, max_messages: int = MAX_MESSAGES):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    raw_messages = data.get("messages", [])
    # Filter empty content
    raw_messages = [m for m in raw_messages if m.get("content", "").strip()]
    sampled = raw_messages[-max_messages:]
    messages = [MessageModel(**m) for m in sampled]

    participants = data.get("participants", [])
    contact_name = None
    for p in participants:
        if p["id"] != "u1":
            contact_name = p["name"]

    return messages, participants, contact_name, len(raw_messages)


def collect_feedback(actions) -> list[FeedbackEntry]:
    print("\n" + "=" * 60)
    print("  📝  FEEDBACK — Help the system learn")
    print("=" * 60)

    feedback = []
    for a in actions:
        print(f"\n  [{a.action_type}] → {a.contact_name}")
        print(f"  Copy: {a.quick_copy}")
        choice = input("  Accept (a) / Reject (r) / Edit (e) / Skip (s): ").strip().lower()

        if choice == "a":
            feedback.append(FeedbackEntry(
                contact_name=a.contact_name,
                action_type=a.action_type,
                decision="Accepted",
            ))
        elif choice == "r":
            feedback.append(FeedbackEntry(
                contact_name=a.contact_name,
                action_type=a.action_type,
                decision="Rejected",
            ))
        elif choice == "e":
            edited = input("  Your version: ").strip()
            feedback.append(FeedbackEntry(
                contact_name=a.contact_name,
                action_type=a.action_type,
                decision="Edited",
                edited_text=edited,
            ))

    if feedback:
        existing = load_collection("feedback", FeedbackEntry)
        save_collection("feedback", existing + feedback)

    return feedback


def main():
    print("=" * 60)
    print("  🚀  SOCIAL LIFE ON AUTO-PILOT  🚀")
    print("  🧬  Value Mapping Edition — Multi-Chat")
    print("=" * 60)

    chat_files = discover_chat_files()
    if not chat_files:
        print(f"\n❌  No chat_*.json files found in: {DATA_DIR}")
        return

    print(f"\n📂  Found {len(chat_files)} chat file(s):")
    for f in chat_files:
        print(f"   • {f.name}")

    # Aggregate results across all chats
    all_profiles = []
    all_verdicts = []
    all_actions = []
    owner_profile = None

    for chat_file in chat_files:
        messages, participants, contact_name, total_count = load_chat_data(chat_file)

        print(f"\n{'─' * 60}")
        print(f"  📨  Processing: {chat_file.name}")
        print(f"      Contact: {contact_name} | {total_count} total msgs | Using last {len(messages)}")
        print(f"{'─' * 60}")

        if len(messages) < 5:
            print(f"  ⏭️   Skipping — too few messages ({len(messages)})")
            continue

        initial_state = {
            "messages": messages,
            "owner_profile": None,
            "profiles": [],
            "previous_profiles": [],
            "feedback_history": [],
            "verdicts": [],
            "actions": [],
        }

        result = app.invoke(initial_state)

        # Collect owner profile from first run (they're all the same person)
        if owner_profile is None and result.get("owner_profile"):
            owner_profile = result["owner_profile"]

        # Accumulate contact-level results
        all_profiles.extend(result.get("profiles", []))
        all_verdicts.extend(result.get("verdicts", []))
        all_actions.extend(result.get("actions", []))

    # ── Print Owner Profile ──────────────────────────────────────────
    if owner_profile:
        print("\n" + "=" * 60)
        print("  👤  YOUR DIGITAL TWIN")
        print("=" * 60)
        print(f"  Vibe       : {owner_profile.vibe_description}")
        print(f"  Style      : {owner_profile.comm_style}")
        print(f"  Formality  : {owner_profile.typing_style.formality_level}")
        print(f"  Slang      : {'✅' if owner_profile.typing_style.use_of_slang else '❌'}")
        print(f"  Emoji/msg  : {owner_profile.typing_style.emoji_density:.2f}")
        print(f"  Topics     : {', '.join(owner_profile.core_topics[:5])}")

    # ── Print All Contact DNA ────────────────────────────────────────
    print("\n" + "=" * 60)
    print(f"  🧬  CONTACT BEHAVIORAL DNA ({len(all_profiles)} contacts)")
    print("=" * 60)
    for p in all_profiles:
        print(f"\n  📋 {p.contact_name}")
        print(f"     Vibe        : {p.vibe_description}")
        print(f"     Reciprocity : {p.reciprocity_ratio:.1%}")
        print(f"     Latency     : {p.avg_latency:.0f}s")
        print(f"     Style       : {p.comm_style}")
        print(f"     Topics      : {', '.join(p.core_topics[:5])}")
        if p.anomalies:
            for a in p.anomalies:
                print(f"     ⚠️  {a.description}")

    # ── Print Strategy Verdicts ──────────────────────────────────────
    print("\n" + "=" * 60)
    print("  📊  STRATEGY VERDICTS (priority-sorted)")
    print("=" * 60)
    for v in sorted(all_verdicts, key=lambda x: x.priority, reverse=True):
        icon = {"Reaction": "💚", "Nudge": "💛", "Deep_Reply": "🔴"}.get(v.recommended_action, "⚪")
        print(f"\n  {icon} {v.contact_name} — Priority {v.priority}/10")
        print(f"     State  : {v.state} | Debt: {v.debt_type} | Drift: {v.sentiment_drift}")
        print(f"     Action : {v.recommended_action}")
        print(f"     Reason : {v.reasoning}")

    # ── Print Proposed Actions ───────────────────────────────────────
    print("\n" + "=" * 60)
    print("  🎯  PROPOSED ACTIONS")
    print("=" * 60)
    for a in all_actions:
        icon = {"Reaction": "👍", "Nudge": "💬", "Deep_Reply": "📝"}.get(a.action_type, "⚪")
        print(f"\n  {icon} [{a.action_type}] → {a.contact_name}")
        print(f"     Copy : {a.quick_copy}")
        print(f"     Why  : {a.rationale}")

    if not all_actions:
        print("\n  ✅  All relationships healthy — no actions needed!")

    # ── Save aggregated collections ──────────────────────────────────
    save_collection("historian_profiles", all_profiles)
    if owner_profile:
        save_collection("owner_profile", [owner_profile])
    save_collection("strategist_verdicts", all_verdicts)
    save_collection("orchestrator_actions", all_actions)
    print("\n💾  Saved all collections.")

    # ── Feedback Loop ────────────────────────────────────────────────
    if all_actions:
        collect_feedback(all_actions)

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
