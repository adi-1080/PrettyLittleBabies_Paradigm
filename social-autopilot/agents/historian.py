"""
agents/historian.py — Agent 1: The Research Agent ("Linguistic FBI Agent")

Performs deep behavioral analysis of chat logs to produce a
ParticipantProfile for each participant. Combines deterministic
pre-computation (timing stats) with LLM-powered linguistic analysis
using structured output for guaranteed Pydantic responses.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import List, Tuple

from langchain_core.messages import SystemMessage, HumanMessage

from config import llm
from state import (
    AgentState,
    MessageModel,
    ParticipantProfile,
    TypingStyle,
    CommunicationPatterns,
)


# ── System Prompt ──────────────────────────────────────────────────────────
HISTORIAN_SYSTEM_PROMPT = """You are **The Linguistic FBI Agent** — a world-class behavioral
analyst who finds hidden patterns in how people communicate.

You will receive:
1. A batch of chat messages from a SINGLE participant.
2. Pre-computed timing statistics for that participant (reply latency,
   peak hours, initiation rate, batch messaging tendency).

Your mission is to produce a deep behavioral fingerprint by analysing:

**Linguistic Traits (TypingStyle):**
- emoji_density: Count emojis per message, return the average as a float.
- avg_word_count: Average words per message (integer).
- formality_level: One of "Formal", "Semi-formal", "Casual", "Very Casual".
- use_of_slang: true if they frequently use slang, abbreviations, or
  non-standard spellings (e.g., "bro", "gonna", "lol", "nah").
- punctuation_style: Describe their punctuation habits, e.g. "Minimalist",
  "Excessive exclamation marks", "Ellipsis lover", "Formal".
- jargon_used: List of technical, industry, or niche terms they use.

**Behavioral Traits (CommunicationPatterns):**
- Use the pre-computed values provided for: reply_latency_seconds,
  peak_activity_hours, initiation_rate, batch_messaging.
- responsiveness: Classify as "Immediate" (< 60s), "Quick" (1-5 min),
  "Normal" (5-30 min), "Deep Thinker (slow)" (30+ min),
  or "Batch Replier" if batch_messaging is true.

**Overall:**
- sentiment_tone: General tone (e.g., "Enthusiastic", "Sarcastic",
  "Supportive but professional", "Brief & curt").
- top_topics: Up to 5 recurring conversation themes.

Return a SINGLE valid JSON object matching the ParticipantProfile schema.
Do NOT wrap in markdown fences.
"""


# ── Emoji regex (Unicode emoji detection) ──────────────────────────────────
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"  # supplemental
    "\U0001FA00-\U0001FA6F"  # chess, extended-A
    "\U0001FA70-\U0001FAFF"  # extended-B
    "\U00002600-\U000026FF"  # misc symbols
    "\U0000FE00-\U0000FE0F"  # variation selectors
    "\U0000200D"             # ZWJ
    "]+",
    flags=re.UNICODE,
)


def _compute_timing_stats(
    participant_id: str,
    all_messages: List[MessageModel],
) -> dict:
    """
    Deterministic pre-computation of timing statistics for a participant.
    Uses functional datetime math — no LLM hallucination for numbers.
    """
    # Separate this participant's messages and the full timeline
    participant_msgs = [m for m in all_messages if m.sender_id == participant_id]
    other_msgs = [m for m in all_messages if m.sender_id != participant_id]

    # ── Reply latency ──────────────────────────────────────────────────
    # Measure time between the last "other" message and this person's reply
    latencies: List[float] = []
    for i, msg in enumerate(all_messages):
        if msg.sender_id == participant_id and i > 0:
            prev = all_messages[i - 1]
            if prev.sender_id != participant_id:
                diff = (msg.timestamp - prev.timestamp).total_seconds()
                if diff > 0:
                    latencies.append(diff)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # ── Peak activity hours ────────────────────────────────────────────
    hour_counts: dict[int, int] = defaultdict(int)
    for m in participant_msgs:
        hour_counts[m.timestamp.hour] += 1

    sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
    peak_hours = [h for h, _ in sorted_hours[:5]]

    # ── Initiation rate ────────────────────────────────────────────────
    # A "conversation initiation" = first message after 1+ hour gap
    GAP_THRESHOLD = 3600  # 1 hour
    initiations = 0
    total_conversations = 0

    for i, msg in enumerate(all_messages):
        if i == 0:
            total_conversations += 1
            if msg.sender_id == participant_id:
                initiations += 1
            continue

        gap = (msg.timestamp - all_messages[i - 1].timestamp).total_seconds()
        if gap >= GAP_THRESHOLD:
            total_conversations += 1
            if msg.sender_id == participant_id:
                initiations += 1

    init_rate = initiations / total_conversations if total_conversations > 0 else 0.0

    # ── Batch messaging ────────────────────────────────────────────────
    # Detect if they send 3+ messages within 60 seconds
    batch_count = 0
    streak = 1
    for i in range(1, len(participant_msgs)):
        diff = (participant_msgs[i].timestamp - participant_msgs[i - 1].timestamp).total_seconds()
        if diff <= 60:
            streak += 1
        else:
            if streak >= 3:
                batch_count += 1
            streak = 1
    if streak >= 3:
        batch_count += 1

    is_batch = batch_count >= 2  # at least 2 batch episodes

    return {
        "reply_latency_seconds": round(avg_latency, 1),
        "peak_activity_hours": peak_hours,
        "initiation_rate": round(init_rate, 3),
        "batch_messaging": is_batch,
    }


def _compute_basic_linguistic_stats(
    participant_msgs: List[MessageModel],
) -> dict:
    """Pre-compute emoji density and avg word count deterministically."""
    total_emojis = 0
    total_words = 0
    text_messages = 0

    for m in participant_msgs:
        if not m.content.strip():
            continue
        text_messages += 1
        total_emojis += len(EMOJI_PATTERN.findall(m.content))
        total_words += len(m.content.split())

    return {
        "emoji_density": round(total_emojis / text_messages, 2) if text_messages else 0.0,
        "avg_word_count": total_words // text_messages if text_messages else 0,
    }


def historian_node(state: AgentState) -> dict:
    """
    LangGraph node that invokes the Research Agent (Historian).

    For each participant, pre-computes deterministic timing stats,
    then uses the LLM with structured output for linguistic analysis.

    Reads   : state["messages"]
    Writes  : {"profiles": List[ParticipantProfile]}
    """
    messages = state["messages"]

    # Identify unique participants (exclude "You" / owner)
    participants: dict[str, str] = {}  # id -> name
    for msg in messages:
        if msg.sender_id not in participants:
            participants[msg.sender_id] = msg.sender_name

    profiles: List[ParticipantProfile] = []

    for pid, pname in participants.items():
        print(f"\n🔍  Analyzing participant: {pname} ({pid})...")

        # Pre-compute deterministic stats
        timing_stats = _compute_timing_stats(pid, messages)
        p_msgs = [m for m in messages if m.sender_id == pid]
        ling_stats = _compute_basic_linguistic_stats(p_msgs)

        # Serialize messages for this participant (sample up to 100)
        sample = p_msgs[-100:] if len(p_msgs) > 100 else p_msgs
        chat_block = "\n".join(
            f"[{m.timestamp.isoformat()}] {m.sender_name}: {m.content}"
            for m in sample
            if m.content.strip()
        )

        context = (
            f"Participant: {pname} (ID: {pid})\n\n"
            f"Pre-computed Timing Stats:\n"
            f"  reply_latency_seconds: {timing_stats['reply_latency_seconds']}\n"
            f"  peak_activity_hours: {timing_stats['peak_activity_hours']}\n"
            f"  initiation_rate: {timing_stats['initiation_rate']}\n"
            f"  batch_messaging: {timing_stats['batch_messaging']}\n\n"
            f"Pre-computed Linguistic Stats:\n"
            f"  emoji_density: {ling_stats['emoji_density']}\n"
            f"  avg_word_count: {ling_stats['avg_word_count']}\n\n"
            f"Their messages (most recent {len(sample)}):\n{chat_block}"
        )

        # Use structured output for guaranteed Pydantic parsing
        structured_llm = llm.with_structured_output(ParticipantProfile)

        profile = structured_llm.invoke([
            SystemMessage(content=HISTORIAN_SYSTEM_PROMPT),
            HumanMessage(content=context),
        ])

        # Override LLM values with our deterministic computations
        profile.sender_id = pid
        profile.sender_name = pname
        profile.communication_patterns.reply_latency_seconds = timing_stats["reply_latency_seconds"]
        profile.communication_patterns.peak_activity_hours = timing_stats["peak_activity_hours"]
        profile.communication_patterns.initiation_rate = timing_stats["initiation_rate"]
        profile.communication_patterns.batch_messaging = timing_stats["batch_messaging"]
        profile.typing_style.emoji_density = ling_stats["emoji_density"]
        profile.typing_style.avg_word_count = ling_stats["avg_word_count"]

        profiles.append(profile)

        print(f"   🏛️  {pname}:")
        print(f"      Tone       : {profile.sentiment_tone}")
        print(f"      Formality  : {profile.typing_style.formality_level}")
        print(f"      Emoji/msg  : {profile.typing_style.emoji_density:.2f}")
        print(f"      Init rate  : {profile.communication_patterns.initiation_rate:.1%}")
        print(f"      Latency    : {profile.communication_patterns.reply_latency_seconds:.0f}s")
        print(f"      Topics     : {', '.join(profile.top_topics[:5])}")

    print(f"\n🏛️  Historian produced {len(profiles)} behavioral fingerprint(s).")
    return {"profiles": profiles}
