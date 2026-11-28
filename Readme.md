# Acquill

Your placement-focused DSA learning companion. Acquill chats with you while you prepare for coding interviews, remembers what you struggled with, warns you when prerequisites are weak, and automatically analyses the code you write.

## What it does

- **Placement-ordered DSA guidance:** follows a 35-topic map from programming basics to DP and advanced topics (trie, union-find, Dijkstra), in the order companies actually test.
- **Dependency gate:** starting something new (say, dynamic programming) while recursion is shaky? Acquill tells you, with a quick warm-up question on the weak spot.
- **One-question coding warm-ups:** short 5-10 minute coding tasks drawn from topics you struggled with before. No hints, no answers, just reps.
- **"Not touched for X" reminders:** tracks when you last touched each topic and nudges you to review before it fades.
- **Automatic code tracking:** a background git monitor analyses your uncommitted diffs, figures out the topic, and logs solved/struggled/asked events without you doing anything. On by default; `chat --no-git` turns it off.
- **Progress digest and pattern analysis:** weekly summaries of gains and recurring struggle patterns.
- **Conversation memory:** each chat run remembers its own thread; long-term memory lives in the database, per user.

## What you need

- **Python 3.10+**
- **A Groq API key** (free tier works) - powers chat, analysis, and replies.
- **A Jina AI API key** (free tier works) - powers semantic recall of your past work.

That's it. The database is shared: topics, history, and accounts live in Acquill's Supabase project, isolated per user. No Postgres setup, no connection strings, nothing to host.

## Install

```bash
pip install acquill
```

## Setup (two minutes)

```bash
acquill init      # enter your Groq + Jina keys (database is preconfigured)
acquill signup    # create your account (email + password)
acquill login     # log in
acquill chat      # start learning
```

## Commands

| Command | What it does |
|---|---|
| `acquill init` | First-time setup (API keys) |
| `acquill chat` | Start interactive chat + background git monitoring |
| `acquill chat --no-git` | Chat with auto code analysis turned off |
| `acquill remind` | Check overdue review reminders |
| `acquill digest [--days 7]` | Progress summary for the last N days |
| `acquill patterns` | Recurring struggle-pattern insights |
| `acquill config show` | View configuration (keys masked) |
| `acquill signup` / `login` / `logout` | Account management |
| `acquill whoami` | Show the logged-in user |
| `acquill reset-password` | Send a password-reset email |

## How it works

Each chat message flows through a pipeline: **extract** (topic + solved/struggled/asked) → **store** (confidence in/out, history logged) → **dependencies** (weak-prerequisite check against the DSA map + your history) → **retrieve** (similar past struggles) → **reply** (warm, concise, placement-focused).

Git diffs take a parallel path through the same graph. Quizzes, reminders, digests, and pattern reports are separate scheduled-style flows over the same data. Conversation state is kept in memory per run; everything worth remembering goes to Supabase, fenced per user by row-level security.

## Privacy

- Your Groq/Jina keys stay in a config file **on your machine only**: they are never uploaded anywhere.
- Learning data goes to the shared Acquill database, where row-level security guarantees you can only ever read and write your **own** rows.
- The app ships with a publishable database key, which is safe to embed by design. It grants nothing beyond what the security policies allow.

## Project layout

```
acquill/
├── interface/   # CLI (Typer) + terminal UI (Rich)
├── nodes/       # graph nodes: chat, reminders, digest, patterns
├── graphs/      # LangGraph workflows + in-memory checkpointer
├── models/       # LLM + embedding clients, placement DSA map
├── prompts/     # system prompts (placement voice, quiz, digest)
├── config/      # setup wizard, auth, settings, validators
├── schemas/     # graph state definitions + pydantic schemas
└── utils/       # orchestration API used by the CLI
sql/             # Supabase functions + shared-DB migration
```

## Status & license

Acquill is in active development (`v0.1.0`), MIT licensed: see [LICENSE](https://github.com/Sivam-dev/Acquill/blob/main/LICENSE).
