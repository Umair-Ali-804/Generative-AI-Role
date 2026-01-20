import os

class RAGConfig:
    OPENAI_API_KEY = "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"
    
    BASE_URL = "https://openrouter.ai/api/v1"
    LLM_MODEL = "liquid/lfm-2.5-1.2b-thinking:free"
    LLM_TEMPERATURE = 0.2
    
    EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    
    VECTOR_DB_TYPE = "chroma"
    PERSIST_DIRECTORY = "./chroma_db"
    COLLECTION_NAME = "agentic_rag_docs"
    
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    
    TOP_K_DOCUMENTS = 5
    SIMILARITY_THRESHOLD = 0.7
    
    MAX_ITERATIONS = 5
    ENABLE_SELF_CORRECTION = True
    ENABLE_QUERY_DECOMPOSITION = True

os.environ["OPENAI_API_KEY"] = RAGConfig.OPENAI_API_KEY
