import os
import sys

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.append(project_root)
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- MOCK IMPORT TO FIX RAGAS BUG ---
import sys, types
if 'langchain_community.chat_models.vertexai' not in sys.modules:
    dummy_module = types.ModuleType('langchain_community.chat_models.vertexai')
    dummy_module.ChatVertexAI = None
    sys.modules['langchain_community.chat_models.vertexai'] = dummy_module
# ------------------------------------

import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)
# pyrefly: ignore [missing-import]
from langchain_groq import ChatGroq
from src.llm_engine import get_embedding_function
import warnings

warnings.filterwarnings("ignore")

def create_mock_dataset():
    """
    Creates a mock evaluation dataset with 3 clinical test cases for NSCLC.
    The dataset includes question, answer, contexts, and ground_truth.
    """
    data = {
        "question": [
            "What is the recommended first-line treatment for a patient with metastatic NSCLC who has an EGFR exon 19 deletion?",
            "Are PD-1/PD-L1 inhibitors recommended for patients with active autoimmune diseases?",
            "What dosage adjustment is required for osimertinib in a patient with severe renal impairment?"
        ],
        "answer": [
            "For a patient with metastatic NSCLC and an EGFR exon 19 deletion, osimertinib is the preferred first-line treatment.",
            "No, PD-1/PD-L1 inhibitors are generally contraindicated in patients with active autoimmune diseases due to the risk of severe immune-related adverse events.",
            "Osimertinib does not require any dosage adjustment for patients with severe renal impairment, though they should be monitored closely."
        ],
        "contexts": [
            [
                "NCCN Guidelines for NSCLC recommend targeted therapy for patients with actionable biomarkers.",
                "Osimertinib is listed as a preferred category 1 recommendation for first-line systemic therapy in metastatic NSCLC patients who have discovered EGFR exon 19 deletions or L858R mutations."
            ],
            [
                "Immunotherapy, including PD-1 and PD-L1 inhibitors, can trigger immune-mediated adverse reactions.",
                "Patients with active or previously documented autoimmune disease have contraindications to immunotherapy. Use of immunosuppressive agents is also a contraindication for these inhibitors."
            ],
            [
                "Osimertinib is an EGFR tyrosine kinase inhibitor used for treating NSCLC.",
                "Pharmacokinetic studies indicate that no clinically significant differences in osimertinib exposure were observed in patients with mild, moderate, or severe renal impairment. Therefore, no dose adjustment is recommended."
            ]
        ],
        "ground_truth": [
            "Osimertinib is the preferred category 1 first-line treatment for metastatic NSCLC with EGFR exon 19 deletion.",
            "They are contraindicated for patients with active autoimmune diseases.",
            "No dosage adjustment is required for osimertinib in severe renal impairment."
        ]
    }
    
    # Optional: If you encounter issues with older versions of ragas expecting a list of lists for ground_truths, 
    # you can rename 'ground_truth' to 'ground_truths' and wrap each answer in a list: e.g., [["Osimertinib..."]]
    
    dataset = Dataset.from_dict(data)
    return dataset


def run_evaluation():
    print("Initializing mock evaluation dataset...")
    dataset = create_mock_dataset()

    print("Configuring evaluator LLM and Embeddings...")
    # NOTE: You MUST set your GROQ_API_KEY as an environment variable before running this script
    # os.environ["GROQ_API_KEY"] = "gsk_..."
    
    evaluator_llm = ChatGroq(model_name="openai/gpt-oss-20b", max_tokens=2048)
    evaluator_embeddings = get_embedding_function()

    metrics = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]

    print("Running Ragas evaluation. This may take a minute or two...")
    try:
        results = evaluate(
            dataset=dataset,
            metrics=metrics,
            llm=evaluator_llm,
            embeddings=evaluator_embeddings,
        )
        
        print("\n" + "="*40)
        print("--- Final Evaluation Scores ---")
        print("="*40)
        print(results)
        
        # Export to CSV
        output_file = "evaluation_results.csv"
        df = results.to_pandas()
        df.to_csv(output_file, index=False)
        print(f"\n[SUCCESS] Results successfully exported to {output_file}")
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred during evaluation: {e}")
        print("Please ensure you have set the GROQ_API_KEY environment variable and installed the correct libraries.")

if __name__ == "__main__":
    run_evaluation()
