import os
from typing import List, Dict, Optional
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader, PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate

from config import settings


class RAGPipeline:
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        embedding_model: Optional[str] = None,
        llm_model: Optional[str] = None,
    ):
        # Set API key
        api_key = google_api_key or settings.GOOGLE_API_KEY
        if not api_key:
            raise ValueError("Google API key is required")
        os.environ["GOOGLE_API_KEY"] = api_key
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model or settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True}
        )

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model=llm_model or settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.MAX_TOKENS
        )

        self.vector_store = None
        self.retriever = None

    def load_single_pdf(self, pdf_path: str) -> List:
        """Load a single PDF file."""
        loader = PyPDFLoader(pdf_path)
        return loader.load()

    def load_directory(self, dir_path: str) -> List:
        """Load all PDFs from a directory."""
        loader = PyPDFDirectoryLoader(dir_path)
        return loader.load()

    def chunk_documents(
        self,
        docs: List,
        chunk_size: Optional[int] = None,
        chunk_overlap: Optional[int] = None
    ) -> List:
        """Split documents into chunks."""
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size or settings.CHUNK_SIZE,
            chunk_overlap=chunk_overlap or settings.CHUNK_OVERLAP,
            length_function=len
        )
        return text_splitter.split_documents(docs)

    def create_vector_store(self, chunks: List, persist_dir: Optional[str] = None):
        """Create and persist vector store from chunks."""
        persist_path = persist_dir or str(settings.VECTOR_DB_DIR)
        self.vector_store = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=persist_path
        )

    def load_vector_store(self, persist_dir: Optional[str] = None):
        """Load existing vector store."""
        persist_path = persist_dir or str(settings.VECTOR_DB_DIR)
        self.vector_store = Chroma(
            persist_directory=persist_path,
            embedding_function=self.embeddings
        )

    def create_retriever(self, search_type: str = "similarity", k: Optional[int] = None):
        """Create retriever from vector store."""
        if not self.vector_store:
            raise ValueError("Vector store not initialized.")
        self.retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": k or settings.RETRIEVER_K}
        )

    def build_qa_chain(self, custom_prompt: Optional[str] = None):
        """Build QA chain with retriever."""
        prompt_text = custom_prompt or """You are an assistant for question-answering tasks.
Use the following pieces of retrieved context to answer the question.
If you don't know the answer, just say that you don't know.
Use three sentences maximum and keep the answer concise.

Context: {context}

Question: {input}

Answer:"""

        prompt_template = ChatPromptTemplate.from_template(prompt_text)
        combine_docs = create_stuff_documents_chain(self.llm, prompt_template)
        return create_retrieval_chain(self.retriever, combine_docs)

    def query(self, question: str, return_sources: bool = True) -> Dict:
        """Query the RAG system."""
        if not self.retriever:
            raise ValueError("Retriever not initialized. Call create_retriever() first.")

        chain = self.build_qa_chain()
        response = chain.invoke({"input": question})

        result = {
            "question": question,
            "answer": response.get("answer", "")
        }

        if return_sources:
            result["source_documents"] = [
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in response.get("context", [])
            ]

        return result

    def process_pdf_and_query(
        self,
        pdf_path: str,
        question: str,
        persist_dir: Optional[str] = None
    ) -> Dict:
        """Complete pipeline: load PDF, create vectors, and query."""
        # Load and process PDF
        docs = self.load_single_pdf(pdf_path)
        chunks = self.chunk_documents(docs)
        
        # Create vector store and retriever
        self.create_vector_store(chunks, persist_dir)
        self.create_retriever()
        
        # Query
        return self.query(question)