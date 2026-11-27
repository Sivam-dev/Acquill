"""
Groq Model Configuration for LLM nodes
"""

import os
from langchain_groq import ChatGroq
from langchain_community.embeddings import JinaEmbeddings

# Load configuration lazily to avoid import-time failures
_config_loaded = False
GROQ_API_KEY = None
JINA_API_KEY = None
EXTRACT_MODEL = "openai/gpt-oss-20b"
JINA_MODEL = "jina-embeddings-v2-base-en"

def _load_config():
    """Load configuration once, lazily"""
    global _config_loaded, GROQ_API_KEY, JINA_API_KEY, EXTRACT_MODEL, JINA_MODEL
    
    if _config_loaded:
        return
    
    # Try to load config from settings, fall back to .env
    try:
        from acquill.config.settings import get_config
        config = get_config()
        GROQ_API_KEY = config["providers"]["groq"]["api_key"]
        JINA_API_KEY = config["providers"]["jina"]["api_key"]
        EXTRACT_MODEL = config["providers"]["groq"].get("model", "openai/gpt-oss-20b")
        JINA_MODEL = config["providers"]["jina"].get("model", "jina-embeddings-v2-base-en")
    except Exception:
        # Fall back to .env
        from dotenv import load_dotenv
        load_dotenv()
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        JINA_API_KEY = os.getenv("JINA_API_KEY")
        EXTRACT_MODEL = "openai/gpt-oss-20b"
        JINA_MODEL = "jina-embeddings-v2-base-en"
    
    _config_loaded = True

# Load config immediately so module-level code works
_load_config()

DIFF_ANALYSIS_MODEL = EXTRACT_MODEL
REPLY_MODEL = EXTRACT_MODEL
QUIZ_MODEL = EXTRACT_MODEL
DIGEST_MODEL = EXTRACT_MODEL
PATTERN_MODEL = EXTRACT_MODEL

embeddings = JinaEmbeddings(
    jina_api_key=JINA_API_KEY,
    model_name=JINA_MODEL
)

extract_llm = ChatGroq(
    model=EXTRACT_MODEL,
    temperature=0.7,
    groq_api_key=GROQ_API_KEY
)

diff_analysis_llm = ChatGroq(
    model=DIFF_ANALYSIS_MODEL,
    temperature=0.7,
    groq_api_key=GROQ_API_KEY
)

reply_llm = ChatGroq(
    model=REPLY_MODEL,
    temperature=0.7,
    groq_api_key=GROQ_API_KEY
)

quiz_llm = ChatGroq(
    model=QUIZ_MODEL,
    temperature=0.7,
    groq_api_key=GROQ_API_KEY
)

digest_llm = ChatGroq(
    model=DIGEST_MODEL,
    temperature=0.7,
    groq_api_key=GROQ_API_KEY
)

pattern_llm = ChatGroq(
    model=PATTERN_MODEL,
    temperature=0.7,
    groq_api_key=GROQ_API_KEY
)
