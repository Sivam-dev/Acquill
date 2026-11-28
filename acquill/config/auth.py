import os
import json
from pathlib import Path
import typer
from supabase import create_client, Client

_supabase_client = None
SUPABASE_URL = None
SUPABASE_KEY = None

def _ensure_supabase():
    """Ensure Supabase client is initialized (lazy loading)"""
    global _supabase_client, SUPABASE_URL, SUPABASE_KEY
    
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        from .settings import get_config
        config = get_config()
        SUPABASE_URL = config["database"]["supabase_url"]
        SUPABASE_KEY = config["database"]["supabase_key"]
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        SUPABASE_URL = os.getenv("SUPABASE_URL")
        SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError(
            "SUPABASE_URL and SUPABASE_KEY required.\n"
            "Run 'acquill init' to configure Acquill or add them to .env file.\n"
            "Get them from: https://supabase.com/dashboard/project/_/settings"
        )
    
    _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _supabase_client

@property
def supabase():
    return _ensure_supabase()

class _SupabaseProxy:
    def __getattr__(self, name):
        return getattr(_ensure_supabase(), name)

supabase: Client = _SupabaseProxy()

SESSION_FILE = Path(typer.get_app_dir("acquill")) / "session.json"


def save_session(session):
    """Save access + refresh tokens to the OS config folder for persistence"""
    try:
        SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(SESSION_FILE, 'w') as f:
            json.dump({
                'access_token': session.access_token,
                'refresh_token': session.refresh_token,
            }, f)
    except Exception as e:
        print(f"Warning: Could not save session: {e}")


def restore_session() -> bool:
    """Restore the saved session into the in-memory supabase client.

    Returns False if no session file exists or restoring fails
    (corrupted file, expired/invalid refresh token) - never raises.
    """
    try:
        if not SESSION_FILE.exists():
            return False
        with open(SESSION_FILE, 'r') as f:
            data = json.load(f)
        result = supabase.auth.set_session(
            data['access_token'], data['refresh_token']
        )
        if result.session:
            save_session(result.session)
            return True
        return False
    except Exception:
        return False


def clear_session():
    """Delete saved session file"""
    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
    except Exception:
        pass


def signup(email: str, password: str):
    result = supabase.auth.sign_up({"email": email, "password": password})
    if result.session:
        save_session(result.session)
    return result


def signin(email: str, password: str):
    result = supabase.auth.sign_in_with_password({"email": email, "password": password})
    if result.session:
        save_session(result.session)
    return result


def signout():
    result = supabase.auth.sign_out()
    clear_session()
    return result


def get_current_user():
    user = supabase.auth.get_user()
    return user
