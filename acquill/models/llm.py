"""
Groq Model Configuration for LLM nodes
"""

import os
from langchain_groq import ChatGroq
from langchain_community.embeddings import JinaEmbeddings

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
    
    try:
        from acquill.config.settings import get_config
        config = get_config()
        GROQ_API_KEY = config["providers"]["groq"]["api_key"]
        JINA_API_KEY = config["providers"]["jina"]["api_key"]
        EXTRACT_MODEL = config["providers"]["groq"].get("model", "openai/gpt-oss-20b")
        JINA_MODEL = config["providers"]["jina"].get("model", "jina-embeddings-v2-base-en")
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        JINA_API_KEY = os.getenv("JINA_API_KEY")
        EXTRACT_MODEL = "openai/gpt-oss-20b"
        JINA_MODEL = "jina-embeddings-v2-base-en"
    
    _config_loaded = True

_load_config()


class _LazyClient:
    """Stand-in that builds the real client on first use.

    Importing this module must never fail (even `acquill init` needs to
    import it before any keys exist), so when keys are missing at import
    time we install a proxy and resolve keys when the client is first used.
    """

    def __init__(self, kind):
        self._kind = kind
        self._client = None

    def _build(self):
        groq_key, jina_key = _resolve_keys()
        if self._kind == "embeddings":
            if not jina_key:
                raise ValueError(
                    "JINA_API_KEY is required. "
                    "Run 'acquill init' to set up Acquill."
                )
            return JinaEmbeddings(
                jina_api_key=jina_key,
                model_name=JINA_MODEL
            )
        if not groq_key:
            raise ValueError(
                "GROQ_API_KEY is required. "
                "Run 'acquill init' to set up Acquill."
            )
        return ChatGroq(
            model=EXTRACT_MODEL,
            temperature=0.7,
            groq_api_key=groq_key
        )

    def _get(self):
        if self._client is None:
            self._client = self._build()
        return self._client

    def __getattr__(self, name):
        return getattr(self._get(), name)


def _resolve_keys():
    """Re-read API keys (config file, then .env, then environment)."""
    try:
        from acquill.config.settings import get_config
        config = get_config()
        return (
            config["providers"]["groq"]["api_key"] or None,
            config["providers"]["jina"]["api_key"] or None
        )
    except Exception:
        from dotenv import load_dotenv
        load_dotenv()
        return (os.getenv("GROQ_API_KEY") or None, os.getenv("JINA_API_KEY") or None)


def _build_all():
    """Construct every client eagerly; raises if any key is missing."""
    chat = ChatGroq(
        model=EXTRACT_MODEL,
        temperature=0.7,
        groq_api_key=GROQ_API_KEY
    )
    return {
        "embeddings": JinaEmbeddings(
            jina_api_key=JINA_API_KEY,
            model_name=JINA_MODEL
        ),
        "llm": chat,
    }


try:
    _clients = _build_all()
except Exception:
    _clients = None

if _clients is not None:
    embeddings = _clients["embeddings"]
    llm = _clients["llm"]
else:
    embeddings = _LazyClient("embeddings")
    llm = _LazyClient("chat")
