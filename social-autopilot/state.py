"""
state.py — Pydantic Models & LangGraph State

Core data models for the Social Autopilot pipeline with
Value Mapping, Anomaly Detection, and Digital Twin support.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. MessageModel — maps 1:1 to the JSON chat export
# ---------------------------------------------------------------------------
class MessageModel(BaseModel):
    id: str
    sender_id: str
    sender_name: str
    role: str = "user"
    content: str = ""
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# 2. TypingStyle — linguistic traits
# ---------------------------------------------------------------------------
class TypingStyle(BaseModel):
    emoji_density: float = Field(ge=0.0, description="Average emoji count per message.")
    avg_word_count: int = Field(ge=0, description="Average words per message.")
    formality_level: str = Field(description="Formal / Semi-formal / Casual / Very Casual.")
    use_of_slang: bool = Field(description="Frequently uses slang.")
    punctuation_style: str = Field(description="e.g. Minimalist, Excessive exclamation, Formal.")
    jargon_used: List[str] = Field(default_factory=list, description="Niche terms identified.")


# ---------------------------------------------------------------------------
# 3. Anomaly — deterministic deviation detected in code
# ---------------------------------------------------------------------------
class Anomaly(BaseModel):
    metric: str = Field(description="Which metric deviated, e.g. 'reply_latency'.")
    baseline: float = Field(description="Historical baseline value.")
    current: float = Field(description="Value in the current window.")
    deviation_factor: float = Field(description="current / baseline ratio.")
    description: str = Field(description="Human-readable anomaly summary.")


# ---------------------------------------------------------------------------
# 4. BehavioralDNA — replaces old ParticipantProfile
# ---------------------------------------------------------------------------
class BehavioralDNA(BaseModel):
    contact_name: str
    contact_id: str
    vibe_description: str = Field(description="Baseline tone: sarcasm, support, emotional sharing, etc.")
    reciprocity_ratio: float = Field(
        ge=0.0, le=1.0,
        description="0.0 = they never initiate, 1.0 = they always initiate.",
    )
    avg_latency: float = Field(ge=0.0, description="Average reply latency in seconds.")
    core_topics: List[str] = Field(default_factory=list, description="Up to 5 value anchors.")
    comm_style: str = Field(description="Batcher (sends bursts) or Streamer (steady flow).")
    typing_style: TypingStyle
    peak_activity_hours: List[int] = Field(default_factory=list, description="Peak hours 0-23.")
    anomalies: List[Anomaly] = Field(default_factory=list, description="Detected deviations.")


# ---------------------------------------------------------------------------
# 5. StrategyVerdict — replaces old RelationshipDecay
# ---------------------------------------------------------------------------
class StrategyVerdict(BaseModel):
    contact_name: str
    state: str = Field(description="Active / Stagnant / Debt.")
    debt_type: str = Field(description="None / Shallow (meme/statement) / Deep (question asked).")
    priority: int = Field(ge=1, le=10, description="1 = low, 10 = critical.")
    recommended_action: str = Field(description="Reaction / Nudge / Deep_Reply.")
    sentiment_drift: str = Field(description="Warmer / Stable / Colder vs baseline.")
    anomalies: List[str] = Field(default_factory=list, description="Anomaly summaries forwarded from DNA.")
    reasoning: str = Field(description="Detailed human-readable justification.")


# ---------------------------------------------------------------------------
# 6. ProposedAction — replaces old SocialNudge
# ---------------------------------------------------------------------------
class ProposedAction(BaseModel):
    contact_name: str
    action_type: str = Field(description="Reaction / Nudge / Deep_Reply.")
    quick_copy: str = Field(description="The emoji, short nudge text, or full reply to copy-paste.")
    rationale: str = Field(description="Why this action, referencing behavioral traits.")


# ---------------------------------------------------------------------------
# Wrapper models for structured LLM output (lists)
# ---------------------------------------------------------------------------
class StrategyVerdictList(BaseModel):
    verdicts: List[StrategyVerdict]


class ProposedActionList(BaseModel):
    actions: List[ProposedAction]


# ---------------------------------------------------------------------------
# 7. FeedbackEntry — user Accept / Reject / Edit per action
# ---------------------------------------------------------------------------
class FeedbackEntry(BaseModel):
    contact_name: str
    action_type: str
    decision: str = Field(description="Accepted / Rejected / Edited.")
    edited_text: Optional[str] = Field(default=None, description="User's edited version if Edited.")
    timestamp: datetime = Field(default_factory=datetime.now)


# ---------------------------------------------------------------------------
# 8. AgentState — the global LangGraph state
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    messages: List[MessageModel]
    owner_profile: Optional[BehavioralDNA]
    profiles: List[BehavioralDNA]
    previous_profiles: List[BehavioralDNA]
    feedback_history: List[FeedbackEntry]
    verdicts: List[StrategyVerdict]
    actions: List[ProposedAction]
