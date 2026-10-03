"""
Postgres checkpointer (Supabase) + per-user thread config.

- get_checkpointer(): single process-lifetime PostgresSaver built from
  CHECKPOINT_DB_URL. Calls .setup() once so checkpoint tables exist.
- get_thread_config(): {"configurable": {"thread_id": "<user_id>:main"}}
  derived from the currently logged-in user. Raises if not logged in,
  so there is no path where a wrong or missing user_id becomes thread_id.

NOTE: PostgresSaver.from_conn_string() is a context manager holding the
DB connection pool, so the saver must stay open for the whole CLI run.
We enter it once here and close it via atexit on process exit.
"""

import atexit
import os

from dotenv import load_dotenv

load_dotenv()

_cm = None
_CHECKPOINTER = None


def get_checkpointer():
    """Return the shared PostgresSaver, creating + setting it up once."""
    global _cm, _CHECKPOINTER
    if _CHECKPOINTER is None:
        from langgraph.checkpoint.postgres import PostgresSaver

        db_url = os.getenv("CHECKPOINT_DB_URL")
        if not db_url:
            raise RuntimeError(
                "CHECKPOINT_DB_URL is not set. Add your Supabase Postgres "
                "connection string to .env (see .env.example)."
            )
        _cm = PostgresSaver.from_conn_string(db_url)
        _CHECKPOINTER = _cm.__enter__()
        _CHECKPOINTER.setup()
        atexit.register(_cm.__exit__, None, None, None)
    return _CHECKPOINTER


def get_thread_id() -> str:
    """One continuous thread per user, forever: '<user_id>:main'."""
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
    return f"{user_id}:main"


def get_thread_config() -> dict:
    """LangGraph invoke config pinning this call to the user's thread."""
    return {"configurable": {"thread_id": get_thread_id()}}
