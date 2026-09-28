"""
Groq Model Configuration for LLM nodes
"""

import os
from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

EXTRACT_MODEL = "openai/gpt-oss-20b"
DIFF_ANALYSIS_MODEL = "openai/gpt-oss-20b"
REPLY_MODEL = "openai/gpt-oss-20b"
QUIZ_MODEL = "openai/gpt-oss-20b"
DIGEST_MODEL = "openai/gpt-oss-20b"
PATTERN_MODEL = "openai/gpt-oss-20b"

embeddings = OllamaEmbeddings(
    model="nomic-embed-text",
    base_url="http://localhost:11434"
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
