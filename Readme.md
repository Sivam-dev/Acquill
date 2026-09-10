═╦══════════════════════════════════════════════════════════════════════════════════════════════════════════
 ║ 🧠 LEARNING COMPANION SYSTEM ║
═╩══════════════════════════════════════════════════════════════════════════════════════════════════════════

A Memory-Driven, Data-Grounded AI Learning Agent Concept.

> **"The data decides; the LLM narrates."**

Traditional LLM chat interfaces frequently hallucinate learner progress, struggle counts, and retention decay. This system is designed to compute all pattern detection, topic confidence scoring, and memory decay deterministically in a structured relational database with vector capabilities (`pgvector`). The LLM's role is strictly constrained to extracting structured facts from free-form text and generating empathetic, data-grounded responses.


┌── PLANNED CORE FEATURES
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘

• **Deterministic Topic & Mastery Tracking**: Automatically track confidence levels for topics explicitly mentioned by the learner, adjusting scores based on problem outcomes (solved vs. struggled).

• **RAG Context Recall (Historical Memory)**: Perform vector similarity search over historical learner interactions to ground responses in past experiences using `pgvector`.

• **Automatic Struggle Pattern Detection**: Normalize and log fine-grained struggle tags (e.g., `hashmap_lookup`, `recursion_base_case`) and trigger automated alerts when thresholds are reached.

• **Proactive Memory Decay (Review Queue)**: Background monitoring worker flags inactive topics as "fading" and pushes them to a review queue before retention degrades.

• **LLM-Free Analytics & Insights**: Direct SQL aggregate queries powering real-time dashboards with zero LLM API latency or cost overhead.


┌── SYSTEM WORKFLOW (THE 7-STAGE PIPELINE)
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘

```text
[ Learner Input ]
       │
       ▼
┌─────────────────────────┐
│ 1. EXTRACT (LLM)        │ Parse text into structured JSON (mentioned topics & struggle tags)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 2. RESOLVE TOPICS       │ Match against existing learner topics or register new ones
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 3. RETRIEVE (RAG)       │ Vector similarity search over past messages (pgvector)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 4. UPDATE MEMORY (LTM)  │ Update topic confidence (+/-), log struggle tag, refresh timestamp
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 5. DETECT PATTERNS      │ Count struggle tag frequency per topic; trigger flag if threshold met
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 6. RESPOND (LLM)        │ Compose reply driven by Stage 5 state (Acknowledge / Pattern / Recommend)
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│ 7. PERSIST              │ Transactionally save message, vector embedding, reply, and links
└────────────┬────────────┘
             │
             ▼
[ Real-Time Reply ]
```


┌── PROJECT STATUS & FUTURE DEVELOPMENT
└──────────────────────────────────────────────────────────────────────────────────────────────────────────┘

• **Currently in Active Building Stage**: This project is under active development. Specifications, features, and pipeline components are continuously being updated and expanded during the process.

