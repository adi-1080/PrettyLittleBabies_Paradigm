"""
rerun_orchestrator.py — Re-run ONLY the Orchestrator agent
using existing historian profiles, strategist verdicts, and owner profile.
Loads recent messages from all chat files for context.
"""

import json
from pathlib import Path

# Add parent to path so imports work
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))

from state import MessageModel, ProposedAction, ProposedActionList
from save_collection import load_collection, save_collection
from agents.orchestrator import orchestrator_node

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
COLLECTIONS_DIR = Path(__file__).resolve().parent / "collections"


def load_all_messages(max_per_chat=20):
    """Load last N messages from each chat file."""
    all_msgs = []
    for chat_file in sorted(DATA_DIR.glob("chat_*.json")):
        with open(chat_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw = [m for m in data.get("messages", []) if m.get("content", "").strip()]
        recent = raw[-max_per_chat:]
        for m in recent:
            all_msgs.append(MessageModel(**m))
    return all_msgs


def main():
    print("=" * 60)
    print("  🔄  RE-RUNNING ORCHESTRATOR ONLY")
    print("=" * 60)

    # Load existing collections
    from state import BehavioralDNA, StrategyVerdict

    profiles = load_collection("historian_profiles", BehavioralDNA)
    verdicts = load_collection("strategist_verdicts", StrategyVerdict)
    owner_list = load_collection("owner_profile", BehavioralDNA)
    owner_profile = owner_list[0] if owner_list else None

    print(f"📋 Loaded {len(profiles)} profiles, {len(verdicts)} verdicts")
    print(f"👤 Owner: {owner_profile.contact_name if owner_profile else 'None'}")

    messages = load_all_messages()
    print(f"📨 Loaded {len(messages)} recent messages for context")

    # Build state
    state = {
        "messages": messages,
        "owner_profile": owner_profile,
        "profiles": profiles,
        "verdicts": verdicts,
        "previous_profiles": [],
        "feedback_history": [],
        "actions": [],
    }

    # Run orchestrator
    print("\n🤖 Running orchestrator...\n")
    result = orchestrator_node(state)

    # Print results
    actions = result["actions"]
    print("\n" + "=" * 60)
    print(f"  🎯  {len(actions)} PROPOSED ACTIONS")
    print("=" * 60)
    for a in actions:
        icon = {"Reaction": "👍", "Nudge": "💬", "Deep_Reply": "📝"}.get(a.action_type, "⚪")
        print(f"\n  {icon} [{a.action_type}] → {a.contact_name}")
        print(f"     Copy : {a.quick_copy}")
        print(f"     Why  : {a.rationale}")

    print("\n💾 Saved to collections/orchestrator_actions.json")
    print("=" * 60)


if __name__ == "__main__":
    main()
