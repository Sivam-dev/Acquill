"""
Configuration package - auth and database setup
"""

from .auth import supabase, signup, signin, signout, get_current_user, restore_session
from .settings import (
    get_config,
    load_config,
    save_config,
    config_exists,
    get_config_path,
    migrate_from_env,
    mask_credential,
    reset_config
)
from .validators import validate_groq_key, validate_jina_key, validate_supabase
from .init_wizard import run_init_wizard

__all__ = [
    'supabase',
    'signup',
    'signin',
    'signout',
    'get_current_user',
    'restore_session',
    'get_config',
    'load_config',
    'save_config',
    'config_exists',
    'get_config_path',
    'migrate_from_env',
    'mask_credential',
    'reset_config',
    'validate_groq_key',
    'validate_jina_key',
    'validate_supabase',
    'run_init_wizard'
]
