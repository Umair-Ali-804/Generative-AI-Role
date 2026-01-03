import streamlit as st
import requests
from pathlib import Path
import json

from config import settings

# Page configuration
st.set_page_config(
    page_title="RAG Q&A System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .source-doc {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #1f77b4;
    }
    </style>
""", unsafe_allow_html=True)

# API base URL
API_URL = settings.API_BASE_URL


def check_api_health():
    """Check if API is running."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def upload_pdf(file):
    """Upload PDF to API."""
    files = {"file": (file.name, file, "application/pdf")}
    response = requests.post(f"{API_URL}/upload", files=files)
    return response.json()


def query_rag(question, return_sources=True):
    """Query the RAG system."""
    payload = {
        "question": question,
        "return_sources": return_sources
    }
    response = requests.post(f"{API_URL}/query", json=payload)
    return response.json()


def load_existing_vectors():
    """Load existing vector store."""
    response = requests.post(f"{API_URL}/load-existing-vectors")
    return response.json()


def clear_vectors():
    """Clear vector store."""
    response = requests.delete(f"{API_URL}/clear-vectors")
    return response.json()


# Main app
def main():
    # Header
    st.markdown('<div class="main-header">📚 RAG-based Q&A System</div>', unsafe_allow_html=True)
    
    # Check API health
    if not check_api_health():
        st.error("❌ API is not running! Please start the FastAPI server first.")
        st.code(f"python main.py", language="bash")
        return
    
    st.success("✅ API is running")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Display settings
        st.subheader("Current Settings")
        st.info(f"""
        **LLM Model:** {settings.LLM_MODEL}
        **Embedding Model:** {settings.EMBEDDING_MODEL}
        **Chunk Size:** {settings.CHUNK_SIZE}
        **Retriever K:** {settings.RETRIEVER_K}
        """)
        
        st.divider()
        
        # Management options
        st.subheader("📂 Vector Store Management")
        
        if st.button("🔄 Load Existing Vectors", use_container_width=True):
            with st.spinner("Loading vectors..."):
                try:
                    result = load_existing_vectors()
                    st.success(result.get("message", "Loaded successfully"))
                except Exception as e:
                    st.error(f"Error: {e}")
        
        if st.button("🗑️ Clear Vector Store", use_container_width=True):
            if st.session_state.get("confirm_clear", False):
                with st.spinner("Clearing vectors..."):
                    try:
                        result = clear_vectors()
                        st.success(result.get("message", "Cleared successfully"))
                        st.session_state.confirm_clear = False
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.session_state.confirm_clear = True
                st.warning("Click again to confirm deletion")
    
    # Main content
    tab1, tab2, tab3 = st.tabs(["📤 Upload PDF", "💬 Ask Questions", "📊 Chat History"])
    
    # Tab 1: Upload PDF
    with tab1:
        st.header("Upload and Process PDF")
        
        uploaded_file = st.file_uploader(
            "Choose a PDF file",
            type=["pdf"],
            help="Upload a PDF document to create a knowledge base"
        )
        
        if uploaded_file is not None:
            st.info(f"📄 Selected file: **{uploaded_file.name}** ({uploaded_file.size / 1024:.2f} KB)")
            
            if st.button("🚀 Process PDF", type="primary", use_container_width=True):
                with st.spinner("Processing PDF... This may take a moment."):
                    try:
                        result = upload_pdf(uploaded_file)
                        st.success(f"✅ {result['message']}")
                        st.info(f"Created **{result['chunks_created']}** chunks from the document")
                        
                        # Store success state
                        st.session_state.pdf_uploaded = True
                        st.session_state.last_filename = result['filename']
                        
                    except Exception as e:
                        st.error(f"❌ Error processing PDF: {e}")
        
        # Show last uploaded file
        if st.session_state.get("pdf_uploaded", False):
            st.success(f"✅ Last uploaded: **{st.session_state.get('last_filename', 'Unknown')}**")
    
    # Tab 2: Ask Questions
    with tab2:
        st.header("Ask Questions")
        
        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # Display sources if available
                if message["role"] == "assistant" and "sources" in message:
                    with st.expander("📚 View Sources"):
                        for i, source in enumerate(message["sources"], 1):
                            st.markdown(f"**Source {i}:**")
                            st.markdown(f'<div class="source-doc">{source["content"][:500]}...</div>', 
                                      unsafe_allow_html=True)
                            if source.get("metadata"):
                                st.caption(f"Metadata: {source['metadata']}")
        
        # Chat input
        if question := st.chat_input("Ask a question about your documents..."):
            # Add user message
            st.session_state.messages.append({"role": "user", "content": question})
            
            with st.chat_message("user"):
                st.markdown(question)
            
            # Get response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    try:
                        response = query_rag(question, return_sources=True)
                        answer = response["answer"]
                        sources = response.get("source_documents", [])
                        
                        st.markdown(answer)
                        
                        # Show sources
                        if sources:
                            with st.expander("📚 View Sources"):
                                for i, source in enumerate(sources, 1):
                                    st.markdown(f"**Source {i}:**")
                                    st.markdown(f'<div class="source-doc">{source["content"][:500]}...</div>', 
                                              unsafe_allow_html=True)
                                    if source.get("metadata"):
                                        st.caption(f"Metadata: {source['metadata']}")
                        
                        # Add assistant message
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer,
                            "sources": sources
                        })
                        
                    except requests.exceptions.HTTPError as e:
                        error_msg = "⚠️ Please upload a PDF first before asking questions."
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
                    except Exception as e:
                        error_msg = f"❌ Error: {str(e)}"
                        st.error(error_msg)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_msg
                        })
        
        # Clear chat button
        if st.session_state.messages:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.messages = []
                st.rerun()
    
    # Tab 3: Chat History
    with tab3:
        st.header("Chat History")
        
        if not st.session_state.get("messages"):
            st.info("No chat history yet. Start asking questions!")
        else:
            for i, message in enumerate(st.session_state.messages):
                if message["role"] == "user":
                    st.markdown(f"**🧑 You:** {message['content']}")
                else:
                    st.markdown(f"**🤖 Assistant:** {message['content']}")
                st.divider()
            
            # Export chat history
            if st.button("💾 Export Chat History", use_container_width=True):
                chat_json = json.dumps(st.session_state.messages, indent=2)
                st.download_button(
                    label="Download as JSON",
                    data=chat_json,
                    file_name="chat_history.json",
                    mime="application/json"
                )


if __name__ == "__main__":
    main()