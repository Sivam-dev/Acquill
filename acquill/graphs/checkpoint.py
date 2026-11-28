"""
In-memory checkpointer + per-session thread config.

Checkpoints are SHORT-TERM memory only, scoped to ONE CLI run and ONE
process: a single InMemorySaver per process means nothing is shared
across runs and nothing touches the database.

- One thread per run: '<user_id>:<run-uuid>' (uuid4 generated once per
  process). A new run always starts with a fresh, empty conversation;
  two runs never share a thread.
- When the process exits, the saver is garbage-collected with it. There
  are no leftover threads to clean up and no locks to hold.
- Long-term data lives in our own Supabase tables (topics,
  topic_history, documents), never in checkpoints.

SessionLostError is kept so existing callers can keep treating a lost
session as fatal; with an in-memory saver it is never raised here.
"""

import threading
import uuid

from langgraph.checkpoint.memory import InMemorySaver


class SessionLostError(RuntimeError):
    """This run's session is gone; the session cannot continue."""


_SESSION_LOST_MSG = "Session lost, please restart Acquill."

_CHECKPOINTER = None
_THREAD_ID = None
_INITIALIZED = False
_SESSION_GUARD = threading.RLock()


def get_checkpointer():
    """Return the shared in-process saver, creating it once."""
    global _CHECKPOINTER
    if _CHECKPOINTER is None:
        _CHECKPOINTER = InMemorySaver()
    return _CHECKPOINTER


def _user_id() -> str:
    """Resolve the logged-in user's id. Raises if not logged in."""
    from acquill.config.auth import get_current_user

    result = get_current_user()
    user = getattr(result, "user", None)
    if isinstance(result, dict):
        user = result.get("user", user)
    user_id = getattr(user, "id", None)
    if isinstance(user, dict):
        user_id = user.get("id", user_id)
    if not user_id:
        raise RuntimeError(
            "Not logged in: cannot resolve thread_id. "
            "Run login first so checkpoints stay tied to your user."
        )
    return user_id


def get_thread_id() -> str:
    """One thread per CLI run: '<user_id>:<run-uuid>' (fresh each run)."""
    global _THREAD_ID
    if _THREAD_ID is None:
        _THREAD_ID = f"{_user_id()}:{uuid.uuid4()}"
    return _THREAD_ID


def ensure_session_alive() -> None:
    """No-op probe: in-memory sessions cannot drop mid-run."""
    with _SESSION_GUARD:
        init_session()


def init_session() -> str:
    """Once per run: resolve thread id. Safe to call repeatedly."""
    global _INITIALIZED
    with _SESSION_GUARD:
        if _INITIALIZED:
            return _THREAD_ID
        get_thread_id()
        get_checkpointer()
        _INITIALIZED = True
        return _THREAD_ID


def get_thread_config() -> dict:
    """LangGraph invoke config pinning this run's calls to its thread."""
    return {"configurable": {"thread_id": init_session()}}
