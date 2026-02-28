"""
state.py — Pydantic Models & LangGraph State

Defines the core data models for the Social Autopilot pipeline
with deep Behavioral Fingerprinting capabilities.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. MessageModel — maps 1:1 to the JSON chat export
# ---------------------------------------------------------------------------
class MessageModel(BaseModel):
    """A single message from an exported WhatsApp/Discord JSON log."""

    id: str
    sender_id: str
    sender_name: str
    role: str = "user"
    content: str = ""
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# 2. TypingStyle — linguistic traits per participant
# ---------------------------------------------------------------------------
class TypingStyle(BaseModel):
    """Captures *how* someone types — their linguistic fingerprint."""

    emoji_density: float = Field(
        ge=0.0,
        description="Average emoji count per message.",
    )
    avg_word_count: int = Field(
        ge=0,
        description="Average number of words per message.",
    )
    formality_level: str = Field(
        description="One of 'Formal', 'Semi-formal', 'Casual', 'Very Casual'.",
    )
    use_of_slang: bool = Field(
        description="Whether the participant frequently uses slang.",
    )
    punctuation_style: str = Field(
        description="E.g. 'Minimalist', 'Excessive exclamation marks', 'Formal'.",
    )
    jargon_used: List[str] = Field(
        default_factory=list,
        description="Technical or niche terms identified.",
    )


# ---------------------------------------------------------------------------
# 3. CommunicationPatterns — behavioral timing traits
# ---------------------------------------------------------------------------
class CommunicationPatterns(BaseModel):
    """Captures *when* and *how fast* someone communicates."""

    reply_latency_seconds: float = Field(
        ge=0.0,
        description="Average reply latency in seconds.",
    )
    peak_activity_hours: List[int] = Field(
        default_factory=list,
        description="Peak hours of communication (0–23).",
    )
    initiation_rate: float = Field(
        ge=0.0,
        le=1.0,
        description="How often this person starts conversations (0.0–1.0).",
    )
    responsiveness: str = Field(
        description="E.g. 'Immediate', 'Deep Thinker (slow)', 'Batch Replier'.",
    )
    batch_messaging: bool = Field(
        description="True if the participant sends multiple messages in rapid succession.",
    )


# ---------------------------------------------------------------------------
# 4. ParticipantProfile — master container per participant
# ---------------------------------------------------------------------------
class ParticipantProfile(BaseModel):
    """
    Complete behavioral fingerprint for a single chat participant.
    Output of Agent 1 (The Historian / Research Agent).
    """

    sender_id: str
    sender_name: str
    typing_style: TypingStyle
    communication_patterns: CommunicationPatterns
    sentiment_tone: str = Field(
        description="General tone, e.g. 'Enthusiastic', 'Sarcastic', 'Brief & curt'.",
    )
    top_topics: List[str] = Field(
        default_factory=list,
        description="Up to 5 recurring conversation themes.",
    )


# ---------------------------------------------------------------------------
# 5. RelationshipDecay — output of the Strategist agent
# ---------------------------------------------------------------------------
class RelationshipDecay(BaseModel):
    """
    Decision-logic model that converts the Historian's profile
    into an actionable alert about relationship health.
    """

    contact_name: str
    decay_score: int = Field(
        ge=0,
        le=100,
        description="0 = Best Friends, 100 = Ghosted.",
    )
    risk_factor: str = Field(
        description="Reason for the score, e.g. '90% deviation from usual vibe'.",
    )
    is_priority: bool = Field(
        description="True when the user should be notified urgently.",
    )


# ---------------------------------------------------------------------------
# 6. SocialNudge — output of the Orchestrator agent
# ---------------------------------------------------------------------------
class SocialNudge(BaseModel):
    """
    A ready-to-send action item for the user.
    The 'Human-in-the-Loop' layer that reduces cognitive load.
    """

    contact_name: str
    nudge_type: str = Field(
        description="E.g. 'Follow-up', 'Check-in', or 'Meme-share'.",
    )
    generated_draft: str = Field(
        description="AI-written message text ready to send.",
    )
    rationale: str = Field(
        description="Why the AI wrote this, e.g. 'They mentioned a job interview'.",
    )


# ---------------------------------------------------------------------------
# 7. AgentState — the global LangGraph state
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    """
    Global state that flows through the LangGraph pipeline.
    Each node reads and updates the relevant keys.
    """

    messages: List[MessageModel]
    profiles: List[ParticipantProfile]
    alerts: List[RelationshipDecay]
    final_recommendations: List[SocialNudge]
