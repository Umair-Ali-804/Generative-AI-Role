# RAG-based Question Answering System

A complete end-to-end Retrieval-Augmented Generation (RAG) application with FastAPI backend and Streamlit frontend.

## 🏗️ Project Structure

```
rag-qa-system/
├── config.py              # Configuration and settings
├── rag_pipeline.py        # RAG pipeline implementation
├── models.py              # Pydantic models
├── main.py                # FastAPI application
├── streamlit_app.py       # Streamlit UI
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── README.md             # This file
├── uploads/              # Directory for uploaded PDFs (auto-created)
└── vector_db/            # Directory for vector database (auto-created)
```

## 🚀 Features

- **PDF Upload & Processing**: Upload single or multiple PDF documents
- **Vector Store Management**: Create, load, and clear vector databases
- **Question Answering**: Ask questions about uploaded documents
- **Source Attribution**: View source documents for each answer
- **Chat History**: Track conversation history
- **RESTful API**: FastAPI backend with automatic documentation
- **Modern UI**: Streamlit interface with real-time updates

## 📋 Prerequisites

- Python 3.8+
- Google API Key (for Gemini LLM)

## 🔧 Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd rag-qa-system
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY
```

## 🎯 Usage

### Option 1: Run Both Servers Separately

**Terminal 1 - Start FastAPI backend:**
```bash
python main.py
```
API will be available at: `http://localhost:8000`
API documentation: `http://localhost:8000/docs`

**Terminal 2 - Start Streamlit frontend:**
```bash
streamlit run streamlit_app.py
```
UI will be available at: `http://localhost:8501`

### Option 2: Run with Script

Create a `run.sh` (Linux/Mac) or `run.bat` (Windows) file:

**run.sh:**
```bash
#!/bin/bash
python main.py &
sleep 5
streamlit run streamlit_app.py
```

**run.bat:**
```batch
@echo off
start python main.py
timeout /t 5
streamlit run streamlit_app.py
```

## 📚 API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Document Management
- `POST /upload` - Upload single PDF
- `POST /upload-directory` - Process directory of PDFs
- `POST /load-existing-vectors` - Load existing vector store
- `DELETE /clear-vectors` - Clear vector store

### Query
- `POST /query` - Query the RAG system

## 🎨 Streamlit UI Features

### 1. Upload PDF Tab
- Upload PDF documents
- View upload status
- Track processed chunks

### 2. Ask Questions Tab
- Chat interface for Q&A
- Real-time responses
- Source document viewing
- Chat history

### 3. Chat History Tab
- View full conversation
- Export chat as JSON

### Sidebar
- Configuration display
- Vector store management
- Load/Clear operations

## 🔑 API Usage Examples

### Upload PDF
```python
import requests

files = {"file": open("document.pdf", "rb")}
response = requests.post("http://localhost:8000/upload", files=files)
print(response.json())
```

### Query System
```python
import requests

payload = {
    "question": "What is the main topic?",
    "return_sources": True
}
response = requests.post("http://localhost:8000/query", json=payload)
print(response.json())
```

## ⚙️ Configuration

Edit `config.py` or `.env` file to customize:

- **LLM Model**: Change Gemini model version
- **Embedding Model**: Use different Hugging Face model
- **Chunk Size**: Adjust document splitting
- **Retriever K**: Number of documents to retrieve
- **API Ports**: Change server ports

## 🛠️ Troubleshooting

### API Not Running
```bash
# Check if port 8000 is in use
lsof -i :8000  # Linux/Mac
netstat -ano | findstr :8000  # Windows
```

### Vector Store Issues
- Clear vector store from UI or API
- Delete `vector_db/` directory manually
- Re-upload documents

### Import Errors
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

## 📝 Notes

- First-time embedding model download may take a few minutes
- Large PDFs may take longer to process
- Vector store persists between sessions
- API key is required for LLM functionality

## 🔒 Security

- Never commit `.env` file with real API keys
- Use environment variables for sensitive data
- Implement authentication for production use

## 📄 License

MIT License

## 🤝 Contributing

Contributions welcome! Please open an issue or submit a PR.

## 📧 Support

For issues and questions, please open a GitHub issue.