import os
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

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print(f"🔐 Supabase Auth initialized: {SUPABASE_URL.split('//')[1].split('.')[0]}")


def signup(email: str, password: str):
    result = supabase.auth.sign_up({"email": email, "password": password})
    return result


def signin(email: str, password: str):
    result = supabase.auth.sign_in_with_password({"email": email, "password": password})
    return result


def signout():
    result = supabase.auth.sign_out()
    return result


def get_current_user():
    user = supabase.auth.get_user()
    return user
