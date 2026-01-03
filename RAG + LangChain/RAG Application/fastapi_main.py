from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import shutil
from pathlib import Path
import logging

from config import settings
from models import QueryRequest, QueryResponse, UploadResponse, HealthResponse, ErrorResponse
from rag_pipeline import RAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="RAG API",
    description="FastAPI backend for RAG-based Question Answering",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize RAG pipeline
try:
    rag_pipeline = RAGPipeline()
    logger.info("RAG Pipeline initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize RAG Pipeline: {e}")
    rag_pipeline = None


@app.get("/", response_model=HealthResponse)
async def root():
    """Root endpoint - health check."""
    return {
        "status": "healthy",
        "vector_store_initialized": rag_pipeline.vector_store is not None if rag_pipeline else False
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    return {
        "status": "healthy",
        "vector_store_initialized": rag_pipeline.vector_store is not None
    }


@app.post("/upload", response_model=UploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and process a PDF file."""
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Save uploaded file
        file_path = settings.UPLOAD_DIR / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file_path}")
        
        # Process PDF
        docs = rag_pipeline.load_single_pdf(str(file_path))
        chunks = rag_pipeline.chunk_documents(docs)
        
        # Create vector store
        rag_pipeline.create_vector_store(chunks)
        rag_pipeline.create_retriever()
        
        logger.info(f"Processed {len(chunks)} chunks from {file.filename}")
        
        return {
            "message": "PDF uploaded and processed successfully",
            "filename": file.filename,
            "chunks_created": len(chunks)
        }
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")


@app.post("/upload-directory")
async def upload_directory(directory_path: str):
    """Process all PDFs in a directory."""
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        if not Path(directory_path).exists():
            raise HTTPException(status_code=404, detail="Directory not found")
        
        docs = rag_pipeline.load_directory(directory_path)
        chunks = rag_pipeline.chunk_documents(docs)
        
        rag_pipeline.create_vector_store(chunks)
        rag_pipeline.create_retriever()
        
        return {
            "message": "Directory processed successfully",
            "chunks_created": len(chunks)
        }
    
    except Exception as e:
        logger.error(f"Error processing directory: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Query the RAG system."""
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    if not rag_pipeline.retriever:
        raise HTTPException(
            status_code=400,
            detail="No documents loaded. Please upload a PDF first."
        )
    
    try:
        result = rag_pipeline.query(
            question=request.question,
            return_sources=request.return_sources
        )
        return result
    
    except Exception as e:
        logger.error(f"Error querying RAG: {e}")
        raise HTTPException(status_code=500, detail=f"Error querying: {str(e)}")


@app.post("/load-existing-vectors")
async def load_existing_vectors():
    """Load existing vector store."""
    if not rag_pipeline:
        raise HTTPException(status_code=500, detail="RAG pipeline not initialized")
    
    try:
        rag_pipeline.load_vector_store()
        rag_pipeline.create_retriever()
        
        return {"message": "Vector store loaded successfully"}
    
    except Exception as e:
        logger.error(f"Error loading vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/clear-vectors")
async def clear_vectors():
    """Clear the vector store."""
    try:
        if settings.VECTOR_DB_DIR.exists():
            shutil.rmtree(settings.VECTOR_DB_DIR)
            settings.VECTOR_DB_DIR.mkdir(exist_ok=True)
        
        if rag_pipeline:
            rag_pipeline.vector_store = None
            rag_pipeline.retriever = None
        
        return {"message": "Vector store cleared successfully"}
    
    except Exception as e:
        logger.error(f"Error clearing vectors: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )