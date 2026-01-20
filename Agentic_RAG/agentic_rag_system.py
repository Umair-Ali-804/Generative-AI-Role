from typing import List, Dict, Any
import json
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_classic.schema import Document
from langchain_openai import ChatOpenAI
from config import RAGConfig
from models import (
    QueryClassification, QueryDecomposition, 
    RetrievalEvaluation, GenerationEvaluation
)
from prompts import (
    QUERY_CLASSIFICATION_PROMPT, QUERY_DECOMPOSITION_PROMPT,
    RETRIEVAL_EVALUATION_PROMPT, ANSWER_GENERATION_PROMPT,
    GENERATION_EVALUATION_PROMPT, ANSWER_REFINEMENT_PROMPT
)


class AgenticRAG:
    def __init__(self, config: RAGConfig, vector_store):
        self.config = config
        self.vector_store = vector_store
        
        self.llm = ChatOpenAI(
            model=config.LLM_MODEL,
            openai_api_key=config.OPENAI_API_KEY,
            openai_api_base=config.BASE_URL,
            temperature=config.LLM_TEMPERATURE,
            max_tokens=1024,
            default_headers={
                "HTTP-Referer": "https://company-chatbot.local",
                "X-Title": "Multi-Agent System",
            }
        )
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL
        )

    def _clean_json_response(self, content: str) -> str:
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return content.strip()

    def classify_query(self, query: str) -> QueryClassification:
        prompt = QUERY_CLASSIFICATION_PROMPT.format(query=query)
        response = self.llm.invoke(prompt)
        content = self._clean_json_response(response.content)
        
        try:
            result = json.loads(content)
            return QueryClassification(**result)
        except json.JSONDecodeError:
            return QueryClassification(
                query_type="simple_factual",
                complexity=5,
                requires_decomposition=False,
                reasoning="Default classification due to parsing error"
            )

    def decompose_query(self, query: str) -> QueryDecomposition:
        prompt = QUERY_DECOMPOSITION_PROMPT.format(query=query)
        response = self.llm.invoke(prompt)
        content = self._clean_json_response(response.content)
        
        try:
            result = json.loads(content)
            return QueryDecomposition(**result)
        except json.JSONDecodeError:
            return QueryDecomposition(
                sub_queries=[],
                synthesis_instruction="Combine answers sequentially"
            )

    def retrieve_documents(self, query: str, k: int = None) -> List[Document]:
        k = k or self.config.TOP_K_DOCUMENTS
        docs = self.vector_store.similarity_search(query, k=k)
        return docs

    def retrieve_with_scores(self, query: str, k: int = None) -> List[tuple]:
        k = k or self.config.TOP_K_DOCUMENTS
        docs_with_scores = self.vector_store.similarity_search_with_score(query, k=k)
        return docs_with_scores

    def evaluate_retrieval(self, query: str, documents: List[Document]) -> RetrievalEvaluation:
        docs_text = "\n\n".join([
            f"Document {i+1}:\n{doc.page_content[:500]}..."
            for i, doc in enumerate(documents)
        ])
        
        prompt = RETRIEVAL_EVALUATION_PROMPT.format(
            query=query,
            docs_text=docs_text
        )
        
        response = self.llm.invoke(prompt)
        content = self._clean_json_response(response.content)
        
        try:
            result = json.loads(content)
            return RetrievalEvaluation(**result)
        except json.JSONDecodeError:
            return RetrievalEvaluation(
                is_sufficient=True,
                relevance_scores=[0.5] * len(documents),
                missing_info=None,
                confidence=0.5
            )

    def generate_answer(self, query: str, documents: List[Document], 
                       context: Dict[str, Any] = None) -> str:
        docs_text = "\n\n".join([
            f"Document {i+1} (Source: {doc.metadata.get('source_file', 'unknown')}):\n{doc.page_content}"
            for i, doc in enumerate(documents)
        ])
        
        context_str = ""
        if context:
            context_str = f"\n\nAdditional Context:\n{json.dumps(context, indent=2)}"
        
        prompt = ANSWER_GENERATION_PROMPT.format(
            query=query,
            docs_text=docs_text,
            context_str=context_str
        )
        
        response = self.llm.invoke(prompt)
        return response.content

    def evaluate_generation(self, query: str, answer: str, 
                           documents: List[Document]) -> GenerationEvaluation:
        docs_text = "\n\n".join([
            f"Doc {i+1}: {doc.page_content[:300]}..."
            for i, doc in enumerate(documents)
        ])
        
        prompt = GENERATION_EVALUATION_PROMPT.format(
            query=query,
            answer=answer,
            docs_text=docs_text
        )
        
        response = self.llm.invoke(prompt)
        content = self._clean_json_response(response.content)
        
        try:
            result = json.loads(content)
            return GenerationEvaluation(**result)
        except json.JSONDecodeError:
            return GenerationEvaluation(
                is_accurate=True,
                is_complete=True,
                is_grounded=True,
                needs_refinement=False,
                issues=[],
                confidence=0.8
            )

    def refine_answer(self, query: str, initial_answer: str, 
                     documents: List[Document], evaluation: GenerationEvaluation) -> str:
        docs_text = "\n\n".join([
            f"Doc {i+1}: {doc.page_content}"
            for i, doc in enumerate(documents)
        ])
        
        issues_text = "\n".join([f"- {issue}" for issue in evaluation.issues])
        
        prompt = ANSWER_REFINEMENT_PROMPT.format(
            query=query,
            initial_answer=initial_answer,
            issues_text=issues_text,
            docs_text=docs_text
        )
        
        response = self.llm.invoke(prompt)
        return response.content

    def process_query(self, query: str, verbose: bool = True) -> Dict[str, Any]:
        result = {
            "query": query,
            "classification": None,
            "decomposition": None,
            "sub_results": [],
            "retrieved_documents": [],
            "retrieval_evaluation": None,
            "initial_answer": None,
            "generation_evaluation": None,
            "final_answer": None,
            "iterations": 0,
            "metadata": {}
        }
        
        if verbose:
            print("\n" + "="*70)
            print("STEP 1: QUERY CLASSIFICATION")
            print("="*70)
        
        classification = self.classify_query(query)
        result["classification"] = classification.dict()
        
        if verbose:
            print(f"Query Type: {classification.query_type}")
            print(f"Complexity: {classification.complexity}/10")
            print(f"Requires Decomposition: {classification.requires_decomposition}")
            print(f"Reasoning: {classification.reasoning}")
        
        if classification.requires_decomposition and self.config.ENABLE_QUERY_DECOMPOSITION:
            if verbose:
                print("\n" + "="*70)
                print("STEP 2: QUERY DECOMPOSITION")
                print("="*70)
            
            decomposition = self.decompose_query(query)
            result["decomposition"] = decomposition.dict()
            
            if verbose:
                print(f"Decomposed into {len(decomposition.sub_queries)} sub-queries:")
                for sq in decomposition.sub_queries:
                    print(f"  {sq.order}. {sq.question}")
            
            sub_answers = {}
            for sub_query in sorted(decomposition.sub_queries, key=lambda x: x.order):
                if verbose:
                    print(f"\n  Processing sub-query {sub_query.order}: {sub_query.question}")
                
                sub_docs = self.retrieve_documents(sub_query.question, k=3)
                sub_answer = self.generate_answer(sub_query.question, sub_docs)
                sub_answers[sub_query.order] = sub_answer
                
                result["sub_results"].append({
                    "sub_query": sub_query.question,
                    "answer": sub_answer
                })
            
            synthesis_context = {
                "sub_answers": sub_answers,
                "synthesis_instruction": decomposition.synthesis_instruction
            }
            
            documents = self.retrieve_documents(query)
            result["retrieved_documents"] = [doc.page_content for doc in documents]
            answer = self.generate_answer(query, documents, context=synthesis_context)
        
        else:
            if verbose:
                print("\n" + "="*70)
                print("STEP 2: DOCUMENT RETRIEVAL")
                print("="*70)
            
            documents = self.retrieve_documents(query)
            result["retrieved_documents"] = [doc.page_content for doc in documents]
            
            if verbose:
                print(f"Retrieved {len(documents)} documents")
            
            if verbose:
                print("\n" + "="*70)
                print("STEP 3: RETRIEVAL EVALUATION")
                print("="*70)
            
            retrieval_eval = self.evaluate_retrieval(query, documents)
            result["retrieval_evaluation"] = retrieval_eval.dict()
            
            if verbose:
                print(f"Sufficient: {retrieval_eval.is_sufficient}")
                print(f"Confidence: {retrieval_eval.confidence}")
                if not retrieval_eval.is_sufficient:
                    print(f"Missing Info: {retrieval_eval.missing_info}")
            
            if verbose:
                print("\n" + "="*70)
                print("STEP 4: ANSWER GENERATION")
                print("="*70)
            
            answer = self.generate_answer(query, documents)
        
        result["initial_answer"] = answer
        
        if self.config.ENABLE_SELF_CORRECTION:
            if verbose:
                print("\n" + "="*70)
                print("STEP 5: ANSWER EVALUATION & REFINEMENT")
                print("="*70)
            
            for iteration in range(self.config.MAX_ITERATIONS):
                result["iterations"] = iteration + 1
                
                gen_eval = self.evaluate_generation(query, answer, documents)
                result["generation_evaluation"] = gen_eval.dict()
                
                if verbose:
                    print(f"\nIteration {iteration + 1}:")
                    print(f"  Accurate: {gen_eval.is_accurate}")
                    print(f"  Complete: {gen_eval.is_complete}")
                    print(f"  Grounded: {gen_eval.is_grounded}")
                    print(f"  Confidence: {gen_eval.confidence}")
                
                if not gen_eval.needs_refinement or gen_eval.confidence > 0.9:
                    if verbose:
                        print("  ✅ Answer quality satisfactory!")
                    break
                
                if verbose:
                    print(f"  Issues: {gen_eval.issues}")
                    print("  Refining answer...")
                
                answer = self.refine_answer(query, answer, documents, gen_eval)
        
        result["final_answer"] = answer
        
        if verbose:
            print("\n" + "="*70)
            print("FINAL ANSWER")
            print("="*70)
            print(answer)
            print("\n")
        
        return result
