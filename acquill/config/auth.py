import os
import json
from pathlib import Path
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

SESSION_FILE = Path.home() / ".acquill_session.json"


def save_session(session_data):
    """Save session to file for persistence"""
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f)
    except Exception as e:
        print(f"Warning: Could not save session: {e}")


def load_session_data():
    """Load session data from file if it exists"""
    try:
        if SESSION_FILE.exists():
            with open(SESSION_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return None


def clear_session():
    """Delete saved session file"""
    try:
        if SESSION_FILE.exists():
            SESSION_FILE.unlink()
    except Exception:
        pass


def get_supabase_client():
    """Get supabase client with current session"""
    session_data = load_session_data()
    
    if session_data and session_data.get('access_token'):
        options = {
            'headers': {
                'Authorization': f"Bearer {session_data['access_token']}"
            }
        }
        return create_client(SUPABASE_URL, SUPABASE_KEY, options=options)
    
    return create_client(SUPABASE_URL, SUPABASE_KEY)


supabase = get_supabase_client()


def signup(email: str, password: str):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.auth.sign_up({"email": email, "password": password})
    if result.session:
        save_session({
            'access_token': result.session.access_token,
            'refresh_token': result.session.refresh_token
        })
        global supabase
        supabase = get_supabase_client()
    return result


def signin(email: str, password: str):
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.auth.sign_in_with_password({"email": email, "password": password})
    if result.session:
        save_session({
            'access_token': result.session.access_token,
            'refresh_token': result.session.refresh_token
        })
        global supabase
        supabase = get_supabase_client()
    return result


def signout():
    try:
        supabase.auth.sign_out()
    except:
        pass
    clear_session()
    global supabase
    supabase = get_supabase_client()
    return None


def get_current_user():
    try:
        user = supabase.auth.get_user()
        return user
    except:
        return None
