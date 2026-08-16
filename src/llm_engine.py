from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from src.config import VECTOR_STORE_DIR

def get_embedding_function():
    """
    Initializes and returns a local embedding model using HuggingFaceEmbeddings.
    """
    return HuggingFaceEmbeddings(model_name='NeuML/pubmedbert-base-embeddings')

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
        persist_directory=str(VECTOR_STORE_DIR)
    )
    
    return vectorstore

def generate_response(prompt: str) -> str:
    """
    Generic LLM interaction function.
    """
    return "Response from LLM engine"
