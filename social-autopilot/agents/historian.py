"""
agents/historian.py — Agent 1: The Relationship DNA Profiler

Analyzes long-term chat archives to build a BehavioralDNA per contact.
Separates the owner (Anupam) as a Digital Twin template.
Detects anomalies via deterministic deviation math.
"""

from __future__ import annotations

import re
from collections import defaultdict
from typing import List

from langchain_core.messages import SystemMessage, HumanMessage

from config import llm
from save_collection import save_collection, save_single
from state import (
    AgentState,
    MessageModel,
    BehavioralDNA,
    TypingStyle,
    Anomaly,
)


OWNER_ID = "u1"

HISTORIAN_SYSTEM_PROMPT = """You are **The Relationship Historian** — your job is to analyze
long-term chat archives and build a "Behavioral DNA" for a participant.

You will receive:
1. A batch of chat messages from a SINGLE participant.
2. Pre-computed deterministic stats (latency, reciprocity, comm_style, emoji density, word count, peak hours).

Your mission — produce a deep Behavioral DNA by analysing:

**Relationship Baseline:**
- vibe_description: What is the baseline tone of this relationship?
  Is it built on sarcasm, professional support, deep emotional sharing,
  memes, casual banter, or collaboration? Be specific and concise.

**Linguistic Traits (TypingStyle):**
- formality_level: One of "Formal", "Semi-formal", "Casual", "Very Casual".
- use_of_slang: true if they frequently use slang, abbreviations, non-standard spellings.
- punctuation_style: Describe habits — "Minimalist", "Excessive exclamation", "Ellipsis lover", etc.
- jargon_used: List technical or niche terms they use.
- (emoji_density and avg_word_count are pre-computed — use the provided values)

**Value Anchors:**
- core_topics: Up to 5 recurring themes that define this bond (e.g. "Blender renders", "AI Marketing", "gym talk").

Return a SINGLE valid JSON object matching the BehavioralDNA schema.
Use the pre-computed values exactly as provided for: reciprocity_ratio, avg_latency,
comm_style, peak_activity_hours, emoji_density, avg_word_count.
Do NOT wrap in markdown fences.
"""

EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)


def _compute_stats(pid: str, all_messages: List[MessageModel]) -> dict:
    p_msgs = [m for m in all_messages if m.sender_id == pid]
    other_msgs = [m for m in all_messages if m.sender_id != pid]

    # Reply latency
    latencies: List[float] = []
    for i, msg in enumerate(all_messages):
        if msg.sender_id == pid and i > 0:
            prev = all_messages[i - 1]
            if prev.sender_id != pid:
                diff = (msg.timestamp - prev.timestamp).total_seconds()
                if diff > 0:
                    latencies.append(diff)
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # Peak hours
    hour_counts: dict[int, int] = defaultdict(int)
    for m in p_msgs:
        hour_counts[m.timestamp.hour] += 1
    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
    peak_hours = [h for h, _ in sorted_hours[:5]]

    # Reciprocity (initiation rate)
    GAP_THRESHOLD = 3600
    initiations, total_convos = 0, 0
    for i, msg in enumerate(all_messages):
        if i == 0:
            total_convos += 1
            if msg.sender_id == pid:
                initiations += 1
            continue
        gap = (msg.timestamp - all_messages[i - 1].timestamp).total_seconds()
        if gap >= GAP_THRESHOLD:
            total_convos += 1
            if msg.sender_id == pid:
                initiations += 1
    reciprocity = initiations / total_convos if total_convos > 0 else 0.0

    # Comm style (Batcher vs Streamer)
    batch_count, streak = 0, 1
    for i in range(1, len(p_msgs)):
        diff = (p_msgs[i].timestamp - p_msgs[i - 1].timestamp).total_seconds()
        if diff <= 60:
            streak += 1
        else:
            if streak >= 3:
                batch_count += 1
            streak = 1
    if streak >= 3:
        batch_count += 1
    comm_style = "Batcher" if batch_count >= 2 else "Streamer"

    # Linguistic stats
    total_emojis, total_words, text_count = 0, 0, 0
    for m in p_msgs:
        if not m.content.strip():
            continue
        text_count += 1
        total_emojis += len(EMOJI_PATTERN.findall(m.content))
        total_words += len(m.content.split())

    return {
        "avg_latency": round(avg_latency, 1),
        "peak_activity_hours": peak_hours,
        "reciprocity_ratio": round(reciprocity, 3),
        "comm_style": comm_style,
        "emoji_density": round(total_emojis / text_count, 2) if text_count else 0.0,
        "avg_word_count": total_words // text_count if text_count else 0,
    }


def _detect_anomalies(
    full_stats: dict,
    window_stats: dict,
) -> List[Anomaly]:
    anomalies = []
    checks = [
        ("reply_latency", "avg_latency", "Reply latency"),
        ("emoji_density", "emoji_density", "Emoji usage"),
        ("avg_word_count", "avg_word_count", "Message length"),
    ]
    for metric, key, label in checks:
        baseline = full_stats.get(key, 0)
        current = window_stats.get(key, 0)
        if baseline > 0:
            ratio = current / baseline
            if ratio >= 2.0 or ratio <= 0.5:
                anomalies.append(Anomaly(
                    metric=metric,
                    baseline=baseline,
                    current=current,
                    deviation_factor=round(ratio, 2),
                    description=f"{label}: {ratio:.1f}x deviation from baseline ({baseline} → {current})",
                ))
    return anomalies


def _build_dna(
    pid: str,
    pname: str,
    all_messages: List[MessageModel],
    window_size: int = 30,
) -> BehavioralDNA:
    full_stats = _compute_stats(pid, all_messages)
    p_msgs = [m for m in all_messages if m.sender_id == pid]

    # Window stats for anomaly detection
    recent_window = all_messages[-window_size:]
    window_stats = _compute_stats(pid, recent_window)
    anomalies = _detect_anomalies(full_stats, window_stats)

    # LLM context
    sample = p_msgs[-100:] if len(p_msgs) > 100 else p_msgs
    chat_block = "\n".join(
        f"[{m.timestamp.isoformat()}] {m.sender_name}: {m.content}"
        for m in sample if m.content.strip()
    )

    context = (
        f"Participant: {pname} (ID: {pid})\n\n"
        f"Pre-computed Stats:\n"
        f"  reciprocity_ratio: {full_stats['reciprocity_ratio']}\n"
        f"  avg_latency: {full_stats['avg_latency']}\n"
        f"  comm_style: {full_stats['comm_style']}\n"
        f"  peak_activity_hours: {full_stats['peak_activity_hours']}\n"
        f"  emoji_density: {full_stats['emoji_density']}\n"
        f"  avg_word_count: {full_stats['avg_word_count']}\n\n"
        f"Their messages (most recent {len(sample)}):\n{chat_block}"
    )

    structured_llm = llm.with_structured_output(BehavioralDNA)
    dna = structured_llm.invoke([
        SystemMessage(content=HISTORIAN_SYSTEM_PROMPT),
        HumanMessage(content=context),
    ])

    # Override with deterministic values
    dna.contact_id = pid
    dna.contact_name = pname
    dna.reciprocity_ratio = full_stats["reciprocity_ratio"]
    dna.avg_latency = full_stats["avg_latency"]
    dna.comm_style = full_stats["comm_style"]
    dna.peak_activity_hours = full_stats["peak_activity_hours"]
    dna.typing_style.emoji_density = full_stats["emoji_density"]
    dna.typing_style.avg_word_count = full_stats["avg_word_count"]
    dna.anomalies = anomalies

    return dna


def historian_node(state: AgentState) -> dict:
    messages = state["messages"]

    participants: dict[str, str] = {}
    for msg in messages:
        if msg.sender_id not in participants:
            participants[msg.sender_id] = msg.sender_name

    owner_profile = None
    profiles: List[BehavioralDNA] = []

    for pid, pname in participants.items():
        print(f"\n🔍  Analyzing: {pname} ({pid})...")
        dna = _build_dna(pid, pname, messages)

        if pid == OWNER_ID:
            owner_profile = dna
            print(f"   👤  Owner profile built (Digital Twin)")
        else:
            profiles.append(dna)

        print(f"   🧬  Vibe       : {dna.vibe_description}")
        print(f"   📊  Reciprocity: {dna.reciprocity_ratio:.1%}")
        print(f"   ⏱️  Latency    : {dna.avg_latency:.0f}s")
        print(f"   📡  Style      : {dna.comm_style}")
        print(f"   🎯  Topics     : {', '.join(dna.core_topics[:5])}")
        if dna.anomalies:
            for a in dna.anomalies:
                print(f"   ⚠️  ANOMALY    : {a.description}")

    print(f"\n🏛️  Historian: {len(profiles)} contact DNA(s) + owner profile.")
    save_collection("historian_profiles", profiles)
    if owner_profile:
        save_single("owner_profile", owner_profile)

    return {"profiles": profiles, "owner_profile": owner_profile}
