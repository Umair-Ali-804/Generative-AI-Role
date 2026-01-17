"""
Configuration file for the multi-agent system
"""
from langchain_openai import ChatOpenAI

# API Configuration
BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY = "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"
MODEL = "allenai/molmo-2-8b:free"
MODEL_2 = "arcee-ai/trinity-mini:free"
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'

# LLM Instances
llm = ChatOpenAI(
    model=MODEL,
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base=BASE_URL,
    temperature=0.7,
    max_tokens=1024,
    default_headers={
        "HTTP-Referer": "https://company-chatbot.local",
        "X-Title": "Multi-Agent System",
    }
)

llm_2 = ChatOpenAI(
    model=MODEL_2,
    openai_api_key=OPENROUTER_API_KEY,
    openai_api_base=BASE_URL,
    temperature=0.7,
    max_tokens=1024,
    default_headers={
        "HTTP-Referer": "https://company-chatbot.local",
        "X-Title": "Multi-Agent System",
    }
)

# Agent Configuration
MAX_ITERATIONS = 10
RECURSION_LIMIT = 25