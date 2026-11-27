"""
Postgres checkpointer (Supabase) + per-session thread config.

Checkpoints are SHORT-TERM memory only, scoped to ONE CLI session:

- One thread per run: '<user_id>:<run-uuid>' (uuid4 generated once per
  process). A new run always starts with a fresh, empty conversation;
  two runs never share a thread.
- When the run exits normally, that thread is deleted from the
  checkpoint tables via the checkpointer's own delete_thread(), so the
  database never fills up. Long-term data lives in our own tables
  (topics, topic_history, documents), never in checkpoints.
- At session init, leftover threads from earlier runs of the SAME user
  are deleted (crash/kill leaves them behind). A thread owned by a live
  run is protected by a Postgres advisory lock and is never deleted.
  Other users' threads are never touched, and the current thread is
  never deleted.

NOTE: PostgresSaver.from_conn_string() is a context manager holding the
DB connection pool, so the saver must stay open for the whole CLI run.
We enter it once here and close it via atexit on process exit. atexit
runs LIFO, so the thread-deletion hook runs BEFORE the connection is
closed, and the advisory-lock connection closes after that.
"""

import atexit
import hashlib
import logging
import os
import threading
import uuid

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SessionLostError(RuntimeError):
    """This run's thread lock is gone; the session cannot continue."""


_SESSION_LOST_MSG = "Session lost, please restart Acquill."

_cm = None
_CHECKPOINTER = None
_THREAD_ID = None
_LOCK_CONN = None
_INITIALIZED = False
_EXIT_HOOK_REGISTERED = False
_SESSION_LOST = False
_SESSION_GUARD = threading.RLock()


def get_checkpointer():
    """Return the shared PostgresSaver, creating + setting it up once."""
    global _cm, _CHECKPOINTER
    if _CHECKPOINTER is None:
        from langgraph.checkpoint.postgres import PostgresSaver

        # Try to load from config, fall back to .env
        try:
            from acquill.config.settings import get_config
            config = get_config()
            db_url = config["database"]["checkpoint_db_url"]
        except Exception:
            db_url = os.getenv("CHECKPOINT_DB_URL")
        
        if not db_url:
            raise RuntimeError(
                "CHECKPOINT_DB_URL is not set.\n"
                "Run 'acquill init' to configure Acquill or add your Supabase "
                "Postgres connection string to .env (see .env.example)."
            )
        _cm = PostgresSaver.from_conn_string(db_url)
        _CHECKPOINTER = _cm.__enter__()
        _CHECKPOINTER.setup()
        atexit.register(_cm.__exit__, None, None, None)
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


def _lock_key(thread_id: str) -> int:
    """Stable signed 64-bit advisory-lock key for a thread id."""
    digest = hashlib.blake2b(thread_id.encode("utf-8"), digest_size=8).digest()
    return int.from_bytes(digest, "big", signed=True)


def _acquire_own_lock() -> None:
    """Take this run's advisory lock on a dedicated connection.

    Postgres releases the lock automatically if the process dies, so it
    is a reliable "this run is still alive" signal for cleanup.
    """
    global _LOCK_CONN
    from psycopg import connect
    from psycopg.rows import dict_row

    conn = connect(
        os.getenv("CHECKPOINT_DB_URL"), autocommit=True, row_factory=dict_row
    )
    try:
        conn.execute("SET statement_timeout = 5000")
        conn.execute(
            "SELECT pg_advisory_lock(%s::bigint)",
            (_lock_key(get_thread_id()),),
        )
    except Exception:
        try:
            conn.close()
        except Exception:
            logger.warning(
                "checkpoint lock connection close failed", exc_info=True
            )
        raise
    _LOCK_CONN = conn


def _close_lock_connection() -> None:
    """Close the lock connection (releases the lock). Never raises."""
    global _LOCK_CONN
    if _LOCK_CONN is not None:
        try:
            _LOCK_CONN.close()
        except Exception:
            logger.warning(
                "checkpoint lock connection close failed", exc_info=True
            )
        finally:
            _LOCK_CONN = None


def _mark_session_lost(reason: str, *, exc_info: bool = False) -> None:
    """Set the permanent session-lost flag, log it, and fail closed."""
    global _SESSION_LOST
    _SESSION_LOST = True
    logger.warning("checkpoint session lost: %s", reason, exc_info=exc_info)
    raise SessionLostError(_SESSION_LOST_MSG)


def ensure_session_alive() -> None:
    """Probe this run's thread lock before a graph call; fail closed.

    A dropped lock connection releases the advisory lock, so another
    run's cleanup could delete this session's thread. Re-acquiring would
    not prove the thread survived, so there is no recovery path: once
    the lock is lost the session is over.
    """
    with _SESSION_GUARD:
        if _SESSION_LOST:
            raise SessionLostError(_SESSION_LOST_MSG)
        if not _INITIALIZED:
            init_session()
            return
        if _LOCK_CONN is None:
            _mark_session_lost("lock connection is gone")
        try:
            _LOCK_CONN.execute("SELECT 1")
        except Exception:
            _mark_session_lost("lock connection probe failed", exc_info=True)


def _delete_leftover_threads(checkpointer) -> None:
    """Delete this user's leftover threads from earlier crashed runs.

    Reads ONLY thread ids from the checkpoints table; deletes strictly
    by thread_id. Other users' threads and the current thread are never
    touched, and a thread whose advisory lock is held by a live run is
    skipped.
    """
    current = get_thread_id()
    user_id = _user_id()
    prefix = f"{user_id}:%"
    try:
        rows = checkpointer.conn.execute(
            "SELECT DISTINCT thread_id FROM checkpoints "
            "WHERE thread_id LIKE %s",
            (prefix,),
        ).fetchall()
    except Exception:
        logger.warning(
            "checkpoint cleanup: could not list threads", exc_info=True
        )
        return
    for row in rows:
        thread_id = row["thread_id"]
        if (
            not thread_id
            or not thread_id.startswith(user_id + ":")
            or thread_id == current
        ):
            continue
        key = _lock_key(thread_id)
        try:
            locked = _LOCK_CONN.execute(
                "SELECT pg_try_advisory_lock(%s::bigint) AS locked", (key,)
            ).fetchone()["locked"]
            if not locked:
                continue
            try:
                checkpointer.delete_thread(thread_id)
            finally:
                _LOCK_CONN.execute(
                    "SELECT pg_advisory_unlock(%s::bigint) AS unlocked",
                    (key,),
                )
        except Exception:
            logger.warning(
                "checkpoint cleanup: could not delete thread %s",
                thread_id,
                exc_info=True,
            )


def _delete_current_on_exit() -> None:
    """Delete this run's thread on normal exit. Never raises."""
    if _THREAD_ID is not None and _CHECKPOINTER is not None:
        try:
            _CHECKPOINTER.delete_thread(_THREAD_ID)
        except Exception:
            logger.warning(
                "checkpoint cleanup: could not delete session thread %s",
                _THREAD_ID,
                exc_info=True,
            )


def init_session() -> str:
    """Once per run: resolve thread id, clear leftovers, arm exit cleanup.

    Must be called after login (the thread id embeds the user's id).
    Safe to call repeatedly; does the work only on the first successful
    call. A failed attempt keeps the same thread id and can be retried.
    """
    global _INITIALIZED, _EXIT_HOOK_REGISTERED
    with _SESSION_GUARD:
        if _INITIALIZED:
            return _THREAD_ID
        if _SESSION_LOST:
            raise SessionLostError(_SESSION_LOST_MSG)
        get_thread_id()
        checkpointer = get_checkpointer()
        if _LOCK_CONN is None:
            _acquire_own_lock()
            atexit.register(_close_lock_connection)
        _delete_leftover_threads(checkpointer)
        if not _EXIT_HOOK_REGISTERED:
            atexit.register(_delete_current_on_exit)
            _EXIT_HOOK_REGISTERED = True
        _INITIALIZED = True
        return _THREAD_ID


def get_thread_config() -> dict:
    """LangGraph invoke config pinning this run's calls to its thread."""
    return {"configurable": {"thread_id": init_session()}}
