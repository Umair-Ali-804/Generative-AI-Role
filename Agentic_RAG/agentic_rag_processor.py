from typing import List
from pathlib import Path
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma, FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_classic.schema import Document
from config import RAGConfig


class DocumentProcessor:
    def __init__(self, config: RAGConfig):
        self.config = config
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""],
            length_function=len
        )
        self.embeddings = HuggingFaceEmbeddings(
            model_name=config.EMBEDDING_MODEL
        )
        self.vector_store = None

    def load_pdf_documents(self, pdf_paths: List[str]) -> List[Document]:
        all_documents = []
        
        for pdf_path in pdf_paths:
            print(f"Loading: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            documents = loader.load()
            
            for doc in documents:
                doc.metadata['source_file'] = Path(pdf_path).name
            
            all_documents.extend(documents)
        
        print(f"Loaded {len(all_documents)} pages from {len(pdf_paths)} PDFs")
        return all_documents

    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunks = self.text_splitter.split_documents(documents)
        
        for i, chunk in enumerate(chunks):
            chunk.metadata['chunk_id'] = i
        
        print(f"Created {len(chunks)} chunks")
        return chunks

    def create_vector_store(self, chunks: List[Document]) -> None:
        if self.config.VECTOR_DB_TYPE == "chroma":
            self.vector_store = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                collection_name=self.config.COLLECTION_NAME,
                persist_directory=self.config.PERSIST_DIRECTORY
            )
            self.vector_store.persist()
        else:
            self.vector_store = FAISS.from_documents(
                documents=chunks,
                embedding=self.embeddings
            )
            self.vector_store.save_local(self.config.PERSIST_DIRECTORY)
        
        print(f"Vector store created with {len(chunks)} chunks")

    def load_existing_vector_store(self) -> None:
        if self.config.VECTOR_DB_TYPE == "chroma":
            self.vector_store = Chroma(
                collection_name=self.config.COLLECTION_NAME,
                embedding_function=self.embeddings,
                persist_directory=self.config.PERSIST_DIRECTORY
            )
        else:
            self.vector_store = FAISS.load_local(
                self.config.PERSIST_DIRECTORY,
                self.embeddings
            )
        
        print("Loaded existing vector store")

    def process_and_store(self, pdf_paths: List[str]) -> None:
        documents = self.load_pdf_documents(pdf_paths)
        chunks = self.chunk_documents(documents)
        self.create_vector_store(chunks)
