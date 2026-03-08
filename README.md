## Resona

[Watch Demo Video Here](https://drive.google.com/file/d/19BhnhXHSjK4xEAFthpBFS8SzVR1UEV0V/view)

A multi-agent pipeline built on LangGraph that reads exported chat logs, builds behavioral fingerprints for each participant, and generates context-aware nudges to help you stay in touch with the people who matter.

---

### Problem

Most "relationship tracker" tools reduce friendships to a single metric: days since last message. That tells you nothing about *how* a relationship is actually doing. A friend who sends walls of text every two weeks is fine. A friend who normally replies in seconds but has gone silent for three days is not.

Resona solves this by analyzing *behavioral patterns* — not just timestamps — to determine which relationships genuinely need attention and what kind of message would feel natural to send.

---

### How the Pipeline Works

The system is a three-node LangGraph StateGraph. Each node is an autonomous agent backed by a Groq-hosted LLM (LLaMA 3.3 70B). The shared state flows through the graph and gets enriched at every step.

**Node 1 — The Historian (Research Agent)**

Takes raw chat messages (WhatsApp JSON export format) and produces a `ParticipantProfile` for each person in the conversation. This profile is split into two parts:

- *Typing Style* — emoji density per message, average word count, formality level, slang usage, punctuation habits, and any jargon or technical terms they frequently use.
- *Communication Patterns* — average reply latency (in seconds), peak activity hours, conversation initiation rate (who starts chats more often), whether they tend to batch-send multiple messages in rapid succession, and an overall responsiveness classification.

The timing and counting stats (latency, initiation rate, emoji density, word count) are computed deterministically from the raw data before being sent to the LLM. The LLM only handles qualitative analysis — formality, sentiment, topic extraction — using structured output to guarantee valid Pydantic objects in return. This hybrid approach avoids hallucinated numbers while still leveraging the model for things it is actually good at.

**Node 2 — The Strategist (Decision Agent)**

Receives the behavioral fingerprints and the last-message timestamps, then calculates a Relationship Decay score (0 to 100) for each participant. The scoring goes beyond silence duration:

- Baseline: +10 per day of silence beyond a 7-day threshold.
- If someone who normally initiates 70% of conversations has gone quiet, the score increases — they might be waiting for you.
- If your most recent message was unusually short or stripped of your typical emoji usage, the agent flags a possible "accidental ghosting" signal.
- If someone is classified as a Batch Replier and hasn't sent a batch in a while, the score decreases slightly — they are likely busy, not disengaged.
- The overall sentiment tone is factored in: silence from a naturally "Brief and curt" person is scored differently than silence from someone who is normally "Enthusiastic."

Each alert includes a human-readable risk factor that references specific behavioral traits, not generic warnings.

**Node 3 — The Orchestrator (Output Agent)**

Takes the decay alerts and the behavioral fingerprints, then generates a ready-to-send message draft for each flagged relationship. The draft is tone-matched to the user's own typing style — if you use slang and emojis, the draft uses slang and emojis. If you are more formal, the draft stays formal. The nudge also references specific shared interests pulled from the participant profile.

Each recommendation includes a rationale explaining *why* this particular nudge was generated, grounded in the behavioral data rather than generic reasoning.

---

### Data Flow

```
Raw JSON Chat Export
        |
   [ Historian ]  -->  ParticipantProfile per person
        |                 (TypingStyle + CommunicationPatterns)
        |
   [ Strategist ] -->  RelationshipDecay per person
        |                 (score + behavioral risk factor)
        |
   [ Orchestrator ] --> SocialNudge per flagged person
                          (tone-matched draft + rationale)
```

---

### Project Structure

```
social-autopilot/
    .env                  # GROQ_API_KEY
    pyproject.toml        # uv-compatible project config
    config.py             # LLM initialization (Groq / LLaMA 3.3 70B)
    state.py              # Pydantic models and LangGraph AgentState
    graph.py              # StateGraph wiring (three-node linear chain)
    main.py               # Entry point, loads chat JSON, runs pipeline
    agents/
        historian.py      # Node 1: behavioral fingerprinting
        strategist.py     # Node 2: decay scoring with behavioral context
        orchestrator.py   # Node 3: tone-matched nudge generation

data/
    chat_data.json        # Exported WhatsApp chat in JSON format
```

---

### Running

```bash
cd social-autopilot
echo "GROQ_API_KEY=your_key_here" > .env
uv run main.py
```

---

### Tech Stack

- **LangGraph** — state machine orchestration for the agent pipeline
- **Groq** (LLaMA 3.3 70B) — LLM inference via `langchain-groq`
- **Pydantic v2** — strict schema validation for all inter-agent data
- **Python 3.10+**