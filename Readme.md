# Acquill

[![Python](https://img.shields.io/badge/python-%3E%3D%203.10-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](https://github.com/Sivam-dev/Acquill/blob/main/LICENSE)
[![GitHub release](https://img.shields.io/github/v/release/Sivam-dev/Acquill)](https://github.com/Sivam-dev/Acquill/releases/latest)

Your placement-focused DSA learning companion. Acquill chats with you while you prepare for coding interviews, remembers what you struggled with, warns you when prerequisites are weak, and automatically analyses the code you write.

## Why Acquill?

Interview prep tools either quiz you blindly or forget everything between sessions. Acquill does neither: every message, solved problem, and struggle is logged against a 35-topic placement map, and every future reply uses that history: prerequisite warnings before you start something new, warm-ups drawn from your actual mistakes, and reminders before topics fade.

## Features

- **Placement-ordered DSA guidance**: follows a 35-topic map in the order companies actually test: programming basics → complexity → recursion → arrays/strings → hashing → linked list/stack/queue → trees → graphs → DP → advanced topics (trie, union-find, Dijkstra).
- **Dependency gate**: starting something new while a prerequisite is shaky? Acquill tells you first:
  > You want DP, but recursion is at 20% confidence and you struggled with it 2 days ago. Quick warm-up: write a recursive function that sums a list.
- **One-question coding warm-ups**: short 5-10 minute coding tasks drawn from topics you struggled with before. No hints, no answers, just reps.
- **"Not touched for X" reminders**: tracks when you last touched each topic and nudges you to review before it fades:
  > `recursion` (confidence: 20%, not touched for 3 days)
- **Automatic code tracking**: a background git monitor analyses your uncommitted diffs every 5 minutes, figures out the topic, and logs solved/struggled/asked events without you doing anything. Duplicate diffs are skipped, large diffs are trimmed to fit model limits. On by default; `chat --no-git` turns it off (the welcome panel always shows the current `ON`/`OFF` label).
- **Progress digest and pattern analysis**: weekly summaries of gains and recurring struggle patterns (`digest`, `patterns`).
- **Conversation memory**: each chat run remembers its own thread; long-term memory lives in the database, per user.

## Install

```bash
pip install acquill
```

Requires **Python 3.10+**. No database to set up, no connection strings: the database is shared (see below).

## Getting API keys (free tiers work)

Acquill needs two keys from you. Everything else is preconfigured.

1. **Groq API key** (the LLM for chat and analysis): create one at [console.groq.com](https://console.groq.com), free tier is enough.
2. **Jina AI API key** (embeddings for semantic recall): create one at [jina.ai](https://jina.ai), free tier is enough.

## Setup (two minutes)

```bash
acquill init      # enter your Groq + Jina keys (database is preconfigured)
acquill signup    # create your account (email + password)
acquill login     # log in
acquill chat      # start learning
```

A first session looks like this:

```
$ acquill chat
  [ Acquill banner + Git monitoring: ON (every 300s) ]

▸ I want to start dynamic programming
Acquill: DP builds straight on recursion, and you struggled with
recursion a couple of days ago. Let's warm up first:

📝 Quick warm-up (recursion):
Write a recursive function that sums a list.
```

Your login persists across restarts (tokens are saved on your machine): you only log in again if you `logout` or the session expires server-side. Your API keys are asked exactly once, during `init`.

## Commands

| Command | What it does |
|---|---|
| `acquill init` | First-time setup (Groq + Jina keys). Flags: `--non-interactive`, `--force` |
| `acquill chat` | Start interactive chat + background git monitoring |
| `acquill chat --no-git` | Chat with auto code analysis turned off |
| `acquill remind` | Check overdue review reminders |
| `acquill digest [--days 7]` | Progress summary for the last N days |
| `acquill patterns` | Recurring struggle-pattern insights |
| `acquill config show` | View configuration (keys masked) |
| `acquill config update` / `reset` | Change or wipe stored configuration |
| `acquill signup` / `login` / `logout` | Account management |
| `acquill whoami` | Show the logged-in user |
| `acquill reset-password` | Send a password-reset email |

## Configuration

Settings live in your OS config folder (`%APPDATA%\acquill\config.json` on Windows): created by `init`, editable via `config update`. Environment variables override file values where noted.

| Setting / env var | Default | What it does |
|---|---|---|
| `GIT_CHECK_INTERVAL` | `300` | Seconds between background git-diff checks |
| `GIT_DIFF_MAX_CHARS` | `3000` | Max diff characters sent to the model per analysis |
| `GIT_MONITORING` | `true` | Set `false` to default git monitoring off (overridable per run with `--git` / `--no-git`) |
| `GROQ_API_KEY` / `JINA_API_KEY` |: (required) | Your keys; also accepted via `.env` |

## How it works

Each chat message flows through a pipeline: **extract** (topic + solved/struggled/asked) → **store** (confidence in/out, history logged) → **dependencies** (weak-prerequisite check against the DSA map + your history) → **retrieve** (similar past struggles) → **reply** (warm, concise, placement-focused).

Git diffs take a parallel path through the same graph. Quizzes, reminders, digests, and pattern reports are separate flows over the same data. Conversation state is kept in memory per run and discarded on exit; everything worth remembering goes to Supabase, fenced per user by row-level security.

## Privacy

- Your Groq/Jina keys stay in a config file **on your machine only**: they are never uploaded anywhere.
- Learning data goes to the shared Acquill database, where row-level security guarantees you can only ever read and write your **own** rows.
- The app ships with a publishable database key, which is safe to embed by design. It grants nothing beyond what the security policies allow.

## Troubleshooting

- **`Not logged in`**: run `acquill login` (first time: `init`, then `signup`).
- **`Session expired`**: log in again; your keys are still saved, they are never asked twice.
- **Diff analysis failed / rate limit**: your uncommitted diff is huge; commit or stash unrelated files. Diffs are auto-trimmed, but per-minute model quotas still apply.
- **No banner animation in logs**: by design: piped output prints one still frame with no control codes.

## Project layout

```
acquill/
├── interface/   # CLI (Typer) + terminal UI (Rich)
├── nodes/       # graph nodes: chat, reminders, digest, patterns
├── graphs/      # LangGraph workflows + in-memory checkpointer
├── models/      # LLM + embedding clients, placement DSA map
├── prompts/     # system prompts (placement voice, quiz, digest)
├── config/      # setup wizard, auth, settings, validators
├── schemas/     # graph state definitions + pydantic schemas
└── utils/       # orchestration API used by the CLI
```

## Changelog

- **v0.1.1**: Rewritten readme; shared-database setup (no per-user Supabase config); lazy model clients so the CLI works before keys exist.
- **v0.1.0**: Initial release.

## Status & license

Acquill is in active development (`v0.1.1`), MIT licensed: see [LICENSE](https://github.com/Sivam-dev/Acquill/blob/main/LICENSE).
