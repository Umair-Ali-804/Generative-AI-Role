from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class QueryRequest(BaseModel):
    question: str = Field(..., description="Question to ask the RAG system")
    return_sources: bool = Field(default=True, description="Whether to return source documents")


class SourceDocument(BaseModel):
    content: str
    metadata: Dict


class QueryResponse(BaseModel):
    question: str
    answer: str
    source_documents: Optional[List[SourceDocument]] = None


class UploadResponse(BaseModel):
    message: str
    filename: str
    chunks_created: int


class HealthResponse(BaseModel):
    status: str
    vector_store_initialized: bool


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None