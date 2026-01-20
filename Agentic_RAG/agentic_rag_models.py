from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


class QueryType(str, Enum):
    SIMPLE_FACTUAL = "simple_factual"
    COMPLEX_REASONING = "complex_reasoning"
    COMPARISON = "comparison"
    MULTI_HOP = "multi_hop"
    SUMMARIZATION = "summarization"


class QueryClassification(BaseModel):
    query_type: QueryType = Field(description="Type of query")
    complexity: int = Field(description="Complexity score from 1-10")
    requires_decomposition: bool = Field(description="Whether query needs to be broken down")
    reasoning: str = Field(description="Explanation of classification")


class SubQuery(BaseModel):
    question: str = Field(description="The sub-question")
    order: int = Field(description="Order of execution")
    dependencies: List[int] = Field(default=[], description="Indices of queries this depends on")


class QueryDecomposition(BaseModel):
    sub_queries: List[SubQuery] = Field(description="List of sub-queries")
    synthesis_instruction: str = Field(description="How to combine answers")


class RetrievalEvaluation(BaseModel):
    is_sufficient: bool = Field(description="Are documents sufficient to answer?")
    relevance_scores: List[float] = Field(description="Relevance score for each document")
    missing_info: Optional[str] = Field(description="What information is missing if insufficient")
    confidence: float = Field(description="Confidence in evaluation (0-1)")


class GenerationEvaluation(BaseModel):
    is_accurate: bool = Field(description="Is the answer accurate?")
    is_complete: bool = Field(description="Is the answer complete?")
    is_grounded: bool = Field(description="Is answer grounded in retrieved docs?")
    needs_refinement: bool = Field(description="Does answer need refinement?")
    issues: List[str] = Field(default=[], description="List of issues if any")
    confidence: float = Field(description="Confidence score (0-1)")
