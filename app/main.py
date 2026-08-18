import os
import sys

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.data_loader import load_pdfs, chunk_documents
from src.llm_engine import build_index, load_index, get_hybrid_retriever
from src.config import VECTOR_STORE_DIR

def main():
    if os.path.exists(VECTOR_STORE_DIR) and os.listdir(VECTOR_STORE_DIR):
        print("Vector store already exists. Loading index from disk...")
        vector_store = load_index()
    else:
        print("Loading PDFs...")
        pages = load_pdfs()
        print(f"Loaded {len(pages)} pages.")

        print("Chunking documents...")
        chunks = chunk_documents(pages)
        print(f"Created {len(chunks)} chunks.")

        if not chunks:
            print("Warning: No text could be extracted from the PDFs. They might be scanned images requiring OCR.")
            return

        print("Building and persisting Chroma index...")
        vector_store = build_index(chunks)
        print("Index built successfully.")

    print("Setting up Hybrid Search (BM25 + Semantic Search)...")
    hybrid_retriever = get_hybrid_retriever(vector_store, k=3)

    query = 'What are the contraindications for treatment with PD-1/PD-L1 inhibitors?'
    print(f"\nPerforming hybrid search for query: '{query}'")
    
    results = hybrid_retriever.invoke(query)
    
    print("\n--- Top Results ---")
    for i, doc in enumerate(results, 1):
        document_name = doc.metadata.get('document_name', 'Unknown')
        page_number = doc.metadata.get('page_number', 'Unknown')
        
        print(f"\nResult {i}")
        print(f"Document: {document_name}")
        print(f"Page: {page_number}")
        print(f"Content Snapshot: {doc.page_content[:200]}...")

if __name__ == "__main__":
    main()
