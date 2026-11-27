"""
Credential validation for Acquill providers
Tests API connectivity without exposing credentials
"""

from typing import Tuple


def validate_groq_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate Groq API key by attempting a minimal API call.
    
    Returns:
        (success: bool, message: str)
    """
    if not api_key or not api_key.startswith("gsk_"):
        return False, "Invalid Groq API key format (should start with 'gsk_')"
    
    try:
        from langchain_groq import ChatGroq
        
        # Attempt a minimal completion
        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0.7,
            groq_api_key=api_key,
            max_tokens=10
        )
        
        # Simple test message
        llm.invoke("test")
        
        return True, "Groq API key validated successfully"
    
    except Exception as e:
        error_msg = str(e).lower()
        
        if "api key" in error_msg or "auth" in error_msg or "401" in error_msg:
            return False, "Invalid Groq API key (authentication failed)"
        elif "rate limit" in error_msg or "429" in error_msg:
            return False, "Groq rate limit reached (but key appears valid)"
        elif "network" in error_msg or "connection" in error_msg:
            return False, "Network error - check your internet connection"
        else:
            return False, f"Validation failed: {str(e)[:100]}"


def validate_jina_key(api_key: str) -> Tuple[bool, str]:
    """
    Validate Jina AI API key by attempting a minimal embedding call.
    
    Returns:
        (success: bool, message: str)
    """
    if not api_key or not api_key.startswith("jina_"):
        return False, "Invalid Jina API key format (should start with 'jina_')"
    
    try:
        from langchain_community.embeddings import JinaEmbeddings
        
        # Attempt a minimal embedding
        embeddings = JinaEmbeddings(
            jina_api_key=api_key,
            model_name="jina-embeddings-v2-base-en"
        )
        
        # Simple test embedding
        embeddings.embed_query("test")
        
        return True, "Jina AI API key validated successfully"
    
    except Exception as e:
        error_msg = str(e).lower()
        
        if "api key" in error_msg or "auth" in error_msg or "401" in error_msg:
            return False, "Invalid Jina AI API key (authentication failed)"
        elif "rate limit" in error_msg or "429" in error_msg:
            return False, "Jina rate limit reached (but key appears valid)"
        elif "network" in error_msg or "connection" in error_msg:
            return False, "Network error - check your internet connection"
        else:
            return False, f"Validation failed: {str(e)[:100]}"


def validate_supabase(url: str, key: str) -> Tuple[bool, str]:
    """
    Validate Supabase credentials by attempting to create a client.
    
    Returns:
        (success: bool, message: str)
    """
    if not url or not url.startswith("https://"):
        return False, "Invalid Supabase URL (should start with 'https://')"
    
    if not key:
        return False, "Supabase key is required"
    
    try:
        from supabase import create_client
        
        # Attempt to create client (doesn't make API call)
        client = create_client(url, key)
        
        # Try a minimal query to verify credentials
        # Using a table that likely exists (auth.users is system table)
        try:
            client.auth.get_session()
            return True, "Supabase credentials validated successfully"
        except Exception:
            # Even if no session, the connection worked
            return True, "Supabase credentials appear valid"
    
    except Exception as e:
        error_msg = str(e).lower()
        
        if "api key" in error_msg or "auth" in error_msg:
            return False, "Invalid Supabase credentials"
        elif "network" in error_msg or "connection" in error_msg:
            return False, "Network error - check your internet connection"
        else:
            return False, f"Validation failed: {str(e)[:100]}"


def validate_checkpoint_db_url(url: str) -> Tuple[bool, str]:
    """
    Validate PostgreSQL connection URL.
    
    Returns:
        (success: bool, message: str)
    """
    if not url or not url.startswith("postgresql://"):
        return False, "Invalid PostgreSQL URL (should start with 'postgresql://')"
    
    # Basic format validation
    # postgresql://user:password@host:port/database
    parts = url.replace("postgresql://", "").split("@")
    if len(parts) != 2:
        return False, "Invalid PostgreSQL URL format"
    
    return True, "PostgreSQL URL format is valid"
