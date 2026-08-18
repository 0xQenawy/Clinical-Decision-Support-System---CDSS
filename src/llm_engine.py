from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_classic.retrievers.ensemble import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from src.config import VECTOR_STORE_DIR

def get_embedding_function():
    """
    Initializes and returns a local embedding model using HuggingFaceEmbeddings.
    """
    return HuggingFaceEmbeddings(model_name='BAAI/bge-base-en-v1.5')

def build_index(chunks):
    """
    Takes a list of document chunks, initializes a local Chroma vector database
    using the embedding function, and saves/persists it directly to the 
    vector_store directory defined in the config.
    """
    embedding_function = get_embedding_function()
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_function,
        persist_directory=str(VECTOR_STORE_DIR),
        collection_metadata={"hnsw:space": "cosine"}
    )
    
    return vectorstore

def load_index():
    """
    Loads an existing Chroma vector database from disk.
    """
    embedding_function = get_embedding_function()
    vectorstore = Chroma(
        persist_directory=str(VECTOR_STORE_DIR),
        embedding_function=embedding_function
    )
    return vectorstore

def get_hybrid_retriever(vectorstore, k=3):
    """
    Combines Semantic Search (Chroma) with Keyword Search (BM25) using RRF.
    """
    # 1. Setup Semantic Retriever
    vector_retriever = vectorstore.as_retriever(search_kwargs={"k": k})
    
    # 2. Extract docs from Chroma to build BM25 Retriever
    collection = vectorstore._collection.get()
    texts = collection['documents']
    metadatas = collection['metadatas']
    
    docs = [Document(page_content=t, metadata=m) for t, m in zip(texts, metadatas)]
    bm25_retriever = BM25Retriever.from_documents(docs)
    bm25_retriever.k = k
    
    # 3. Combine them (50% weight for each)
    ensemble_retriever = EnsembleRetriever(
        retrievers=[bm25_retriever, vector_retriever],
        weights=[0.5, 0.5]
    )
    return ensemble_retriever

def generate_response(prompt: str) -> str:
    """
    Generic LLM interaction function.
    """
    return "Response from LLM engine"
