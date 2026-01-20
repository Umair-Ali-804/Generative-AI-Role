import warnings
warnings.filterwarnings('ignore')

from config import RAGConfig
from document_processor import DocumentProcessor
from agentic_rag import AgenticRAG


def setup_system(pdf_files: list[str], rebuild_db: bool = False):
    print("="*70)
    print("AGENTIC RAG SYSTEM - INITIALIZATION")
    print("="*70)
    
    config = RAGConfig()
    
    print("\n📄 Setting up document processor...")
    processor = DocumentProcessor(config)
    
    if rebuild_db:
        print("\n🔨 Building vector database...")
        processor.process_and_store(pdf_files)
    else:
        print("\n📚 Loading existing vector database...")
        processor.load_existing_vector_store()
    
    print("\n🤖 Initializing Agentic RAG system...")
    rag = AgenticRAG(config, processor.vector_store)
    
    print("\n✅ System ready!")
    return rag, processor


def run_example_query(rag: AgenticRAG):
    print("\n" + "="*70)
    print("EXAMPLE QUERY")
    print("="*70)
    
    query = "What is the main topic discussed in the document?"
    result = rag.process_query(query, verbose=True)
    
    return result


def interactive_mode(rag: AgenticRAG):
    print("\n" + "="*70)
    print("INTERACTIVE MODE")
    print("="*70)
    print("Enter your questions (type 'exit' to quit, 'help' for options)")
    print("="*70)
    
    verbose = True
    
    while True:
        query = input("\n🔍 Your question: ").strip()
        
        if query.lower() == 'exit':
            print("👋 Goodbye!")
            break
        
        if query.lower() == 'help':
            print("\nCommands:")
            print("  exit - Exit interactive mode")
            print("  help - Show this help message")
            print("  verbose on - Enable verbose output")
            print("  verbose off - Disable verbose output")
            continue
        
        if query.lower() == 'verbose on':
            verbose = True
            print("✅ Verbose mode enabled")
            continue
        
        if query.lower() == 'verbose off':
            verbose = False
            print("✅ Verbose mode disabled")
            continue
        
        if not query:
            continue
        
        result = rag.process_query(query, verbose=verbose)


def main():
    pdf_files = [
        "./Umair_Ali.pdf"
    ]
    
    rag_system, doc_processor = setup_system(pdf_files, rebuild_db=False)
    
    run_example_query(rag_system)
    
    interactive_mode(rag_system)
    
    print("\n✅ Agentic RAG system demonstration complete!")


if __name__ == "__main__":
    main()
