# Agentic RAG System

A sophisticated Retrieval-Augmented Generation system with query routing, decomposition, and self-correction capabilities.

## Features

- **Query Classification**: Automatically classifies queries by type and complexity
- **Query Decomposition**: Breaks down complex queries into manageable sub-queries
- **Smart Retrieval**: Retrieves relevant documents with similarity scoring
- **Self-Correction**: Evaluates and refines answers iteratively
- **Multi-Document Processing**: Handles multiple PDF documents

## File Structure

```
agentic_rag/
├── config.py              # Configuration settings
├── models.py              # Pydantic data models
├── prompts.py             # All prompt templates
├── document_processor.py  # Document loading and vector store
├── agentic_rag.py        # Main RAG system logic
├── main.py               # Entry point and CLI
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### First Time Setup

1. Place your PDF files in the project directory
2. Update `pdf_files` list in `main.py`
3. Set `rebuild_db=True` in `setup_system()` call
4. Run: `python main.py`

### Subsequent Runs

1. Set `rebuild_db=False` in `setup_system()` call
2. Run: `python main.py`

### Interactive Mode Commands

- Type your question to get an answer
- `help` - Show available commands
- `verbose on` - Enable detailed output
- `verbose off` - Disable detailed output
- `exit` - Quit the program

## Configuration

Edit `config.py` to customize:

- API keys and endpoints
- Model selection
- Chunk sizes
- Retrieval parameters
- Agent behavior

## How It Works

1. **Query Classification**: Determines query type and complexity
2. **Query Decomposition**: (Optional) Breaks complex queries into sub-queries
3. **Document Retrieval**: Fetches relevant documents from vector store
4. **Retrieval Evaluation**: Assesses if retrieved documents are sufficient
5. **Answer Generation**: Creates initial answer from documents
6. **Self-Correction Loop**: Evaluates and refines answer until quality threshold met

## Example

```python
from config import RAGConfig
from document_processor import DocumentProcessor
from agentic_rag import AgenticRAG

config = RAGConfig()
processor = DocumentProcessor(config)
processor.load_existing_vector_store()

rag = AgenticRAG(config, processor.vector_store)
result = rag.process_query("What is the main topic?", verbose=True)

print(result["final_answer"])
```
