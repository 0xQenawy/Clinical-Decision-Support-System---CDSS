import csv
import sys
import os
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.llm_engine import get_embedding_function
from src.config import VECTOR_STORE_DIR
from langchain_community.vectorstores import Chroma

def evaluate_retrieval(csv_path, top_k=3):
    print("Loading vector database...")
    embedding_function = get_embedding_function()
    vectorstore = Chroma(
        persist_directory=str(VECTOR_STORE_DIR),
        embedding_function=embedding_function,
        collection_metadata={"hnsw:space": "cosine"}
    )
    
    hits = 0
    mrr_sum = 0
    total = 0
    
    print(f"\nRunning evaluation on {csv_path} with top_k={top_k}\n")
    start_time = time.time()
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            question = row['Question']
            expected = row['Expected Keyword'].lower()
            
            results = vectorstore.similarity_search_with_relevance_scores(question, k=top_k)
            
            hit = False
            rank = 0
            for i, (doc, score) in enumerate(results):
                if expected in doc.page_content.lower():
                    hit = True
                    rank = i + 1
                    break
            
            total += 1
            if hit:
                hits += 1
                mrr_sum += (1.0 / rank)
                print(f"[HIT] Rank {rank} | Q: {question[:50]}...")
            else:
                print(f"[MISS]        | Q: {question[:50]}...")
                
    elapsed = time.time() - start_time
    
    hit_rate = hits / total if total > 0 else 0
    mrr = mrr_sum / total if total > 0 else 0
    
    print("\n--- Evaluation Results ---")
    print(f"Total Questions: {total}")
    print(f"Hit Rate (@{top_k}): {hit_rate:.2%}")
    print(f"Mean Reciprocal Rank (MRR): {mrr:.3f}")
    print(f"Time Taken: {elapsed:.2f} seconds")

if __name__ == "__main__":
    csv_file = os.path.join(os.path.dirname(__file__), "lung_cancer_test_set.csv")
    evaluate_retrieval(csv_file, top_k=3)
