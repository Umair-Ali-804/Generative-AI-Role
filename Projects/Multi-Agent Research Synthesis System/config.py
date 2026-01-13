import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

class Config:
    
    # API Keys
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "..........")
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "..........")
    
    # LangSmith 
    LANGCHAIN_TRACING_V2: str = os.getenv("LANGCHAIN_TRACING_V2", "false")
    LANGCHAIN_API_KEY: str = os.getenv("LANGCHAIN_API_KEY", "..........")
    LANGCHAIN_PROJECT: str = os.getenv("LANGCHAIN_PROJECT", "research-synthesis-system")
    
    # Model Configuration
    DEFAULT_GPT_MODEL: str = os.getenv("DEFAULT_GPT_MODEL", "gpt-4o")
    DEFAULT_CLAUDE_MODEL: str = os.getenv("DEFAULT_CLAUDE_MODEL", "claude-sonnet-4-20250514")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    
    # System Parameters
    MAX_PAPERS: int = int(os.getenv("MAX_PAPERS", "10"))
    MAX_ITERATIONS: int = int(os.getenv("MAX_ITERATIONS", "2"))
    QUALITY_THRESHOLD: float = float(os.getenv("QUALITY_THRESHOLD", "7.0"))
    
    # Vector Store
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K_RETRIEVAL: int = 5
    
    # Agent Configuration
    PLANNER_TEMPERATURE: float = 0.3
    SUMMARIZER_TEMPERATURE: float = 0.2
    SYNTHESIS_TEMPERATURE: float = 0.4
    CRITIC_TEMPERATURE: float = 0.1
    REFLECTION_TEMPERATURE: float = 0.3
    
    @classmethod
    def validate(cls) -> bool:
        if not cls.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not set in environment")
        if not cls.ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY not set in environment")
        return True
    
    @classmethod
    def enable_langsmith(cls):
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        if cls.LANGCHAIN_API_KEY:
            os.environ["LANGCHAIN_API_KEY"] = cls.LANGCHAIN_API_KEY
        if cls.LANGCHAIN_PROJECT:
            os.environ["LANGCHAIN_PROJECT"] = cls.LANGCHAIN_PROJECT

# Validate on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Warning: {e}")
    print("Please set required API keys in .env file")