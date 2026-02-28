"""
state.py — Pydantic Models & LangGraph State

Defines the core data models for the Social Autopilot pipeline
and the AgentState TypedDict consumed by LangGraph's StateGraph.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, TypedDict

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 1. ChatMessage — the primitive data unit
# ---------------------------------------------------------------------------
class ChatMessage(BaseModel):
    """A single message from an exported chat log (WhatsApp, Discord, etc.)."""

    sender: str
    content: str
    timestamp: datetime


# ---------------------------------------------------------------------------
# 2. RelationalProfile — output of the Historian agent
# ---------------------------------------------------------------------------
class RelationalProfile(BaseModel):
    """
    Summarised "vibe & stats" for a specific friendship.
    Transforms raw chat history into structured knowledge.
    """

    contact_name: str
    interaction_frequency: str = Field(
        description="Label such as 'Daily', 'Weekly', or 'Sporadic'."
    )
    average_response_time: float = Field(
        description="Average response time in hours."
    )
    top_topics: List[str] = Field(
        default_factory=list,
        description="Key shared interests, e.g. ['F1 Racing', 'Node.js'].",
    )
    sentiment_score: float = Field(
        ge=-1.0,
        le=1.0,
        description="General mood of the relationship (-1.0 to 1.0).",
    )


# ---------------------------------------------------------------------------
# 3. RelationshipDecay — output of the Strategist agent
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
        description="Reason for the score, e.g. '3× longer than usual silence'."
    )
    is_priority: bool = Field(
        description="True when the user should be notified urgently."
    )


# ---------------------------------------------------------------------------
# 4. SocialNudge — output of the Orchestrator agent
# ---------------------------------------------------------------------------
class SocialNudge(BaseModel):
    """
    A ready-to-send action item for the user.
    The 'Human-in-the-Loop' layer that reduces cognitive load.
    """

    contact_name: str
    nudge_type: str = Field(
        description="E.g. 'Follow-up', 'Check-in', or 'Meme-share'."
    )
    generated_draft: str = Field(
        description="AI-written message text ready to send."
    )
    rationale: str = Field(
        description="Why the AI wrote this, e.g. 'They mentioned a job interview'."
    )


# ---------------------------------------------------------------------------
# 5. AgentState — the global LangGraph state
# ---------------------------------------------------------------------------
class AgentState(TypedDict):
    """
    Global state that flows through the LangGraph pipeline.
    Each node reads and updates the relevant keys.
    """

    messages: List[ChatMessage]
    profiles: List[RelationalProfile]
    alerts: List[RelationshipDecay]
    final_recommendations: List[SocialNudge]
