import os
import json
from pathlib import Path
import typer
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError(
        "SUPABASE_URL and SUPABASE_KEY required in .env file.\n"
        "Get them from: https://supabase.com/dashboard/project/_/settings"
    )

SESSION_FILE = Path(typer.get_app_dir("acquill")) / "session.json"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


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
    (corrupted file, expired/invalid refresh token) — never raises.
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
            # Re-save: set_session may have refreshed the access token
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
