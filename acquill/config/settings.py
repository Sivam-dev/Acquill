"""
Configuration management for Acquill
Handles loading, saving, and validating user configuration
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional, Any
import typer


def get_config_path() -> Path:
    """Get the path to the user's configuration file"""
    config_dir = Path(typer.get_app_dir("acquill"))
    return config_dir / "config.json"


def config_exists() -> bool:
    """Check if configuration file exists"""
    return get_config_path().exists()


def load_config() -> Optional[Dict[str, Any]]:
    """
    Load configuration from config.json.
    Returns None if config doesn't exist.
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        return None
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        raise RuntimeError(f"Failed to load configuration: {e}")


def save_config(config: Dict[str, Any]) -> None:
    """
    Save configuration to config.json.
    Creates parent directory if it doesn't exist.
    Sets restrictive file permissions on Unix systems.
    """
    config_path = get_config_path()
    
    # Create directory if it doesn't exist
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save configuration
    try:
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Restrict file permissions on Unix systems (chmod 600)
        if os.name != 'nt':  # Not Windows
            os.chmod(config_path, 0o600)
    except Exception as e:
        raise RuntimeError(f"Failed to save configuration: {e}")


def load_from_env() -> Optional[Dict[str, Any]]:
    """
    Load configuration from .env file as fallback.
    Returns None if required variables are missing.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    groq_key = os.getenv("GROQ_API_KEY")
    jina_key = os.getenv("JINA_API_KEY")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    checkpoint_url = os.getenv("CHECKPOINT_DB_URL")
    
    # Check if all required variables exist
    if not all([groq_key, jina_key, supabase_url, supabase_key, checkpoint_url]):
        return None
    
    return {
        "version": "1.0",
        "providers": {
            "groq": {
                "api_key": groq_key,
                "model": "openai/gpt-oss-20b"
            },
            "jina": {
                "api_key": jina_key,
                "model": "jina-embeddings-v2-base-en"
            }
        },
        "database": {
            "supabase_url": supabase_url,
            "supabase_key": supabase_key,
            "checkpoint_db_url": checkpoint_url
        },
        "git_check_interval": int(os.getenv("GIT_CHECK_INTERVAL", "300")),
        "git_monitoring": os.getenv("GIT_MONITORING", "true").lower() == "true"
    }


def get_config() -> Dict[str, Any]:
    """
    Get configuration from config.json or fall back to .env.
    Raises RuntimeError if no configuration is found.
    """
    # Try config.json first
    config = load_config()
    if config is not None:
        return config
    
    # Fall back to .env
    config = load_from_env()
    if config is not None:
        return config
    
    # No configuration found
    raise RuntimeError(
        "No configuration found. Run 'acquill init' to set up Acquill."
    )


def migrate_from_env() -> Dict[str, Any]:
    """
    Import credentials from .env file for initial setup.
    Returns a config dict ready to be saved.
    """
    from dotenv import load_dotenv
    load_dotenv()
    
    return {
        "version": "1.0",
        "providers": {
            "groq": {
                "api_key": os.getenv("GROQ_API_KEY", ""),
                "model": "openai/gpt-oss-20b"
            },
            "jina": {
                "api_key": os.getenv("JINA_API_KEY", ""),
                "model": "jina-embeddings-v2-base-en"
            }
        },
        "database": {
            "supabase_url": os.getenv("SUPABASE_URL", ""),
            "supabase_key": os.getenv("SUPABASE_KEY", ""),
            "checkpoint_db_url": os.getenv("CHECKPOINT_DB_URL", "")
        },
        "git_check_interval": int(os.getenv("GIT_CHECK_INTERVAL", "300")),
        "git_monitoring": os.getenv("GIT_MONITORING", "true").lower() == "true"
    }


def mask_credential(value: str, visible_chars: int = 4) -> str:
    """
    Mask a credential showing only the last few characters.
    Example: "gsk_1234567890abcdef" -> "gsk_****abcdef"
    """
    if not value or len(value) <= visible_chars:
        return "****"
    
    # For keys with prefixes (gsk_, jina_, sb_), show prefix + last chars
    if "_" in value[:10]:
        prefix = value.split("_")[0] + "_"
        masked = prefix + "*" * (len(value) - len(prefix) - visible_chars) + value[-visible_chars:]
    else:
        masked = "*" * (len(value) - visible_chars) + value[-visible_chars:]
    
    return masked


def reset_config() -> None:
    """Delete the configuration file"""
    config_path = get_config_path()
    if config_path.exists():
        config_path.unlink()
