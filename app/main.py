import os
import sys

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)

from src.data_loader import load_pdfs, chunk_documents
from src.llm_engine import build_index

def main():
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

    query = 'What is the target blood pressure for a patient with cardiovascular disease?'
    print(f"\nPerforming similarity search for query: '{query}'")
    
    results = vector_store.similarity_search_with_relevance_scores(query, k=3)
    
    print("\n--- Top 3 Results ---")
    for i, (doc, score) in enumerate(results, 1):
        document_name = doc.metadata.get('document_name', 'Unknown')
        page_number = doc.metadata.get('page_number', 'Unknown')
        
        print(f"\nResult {i}")
        print(f"Score: {score:.4f}")
        print(f"Document: {document_name}")
        print(f"Page: {page_number}")
        print(f"Content Snapshot: {doc.page_content[:200]}...")

if __name__ == "__main__":
    main()
