"""
CDSS FastAPI Backend — Precision Oncology RAG Pipeline
======================================================
Orchestrates the flow between:
  • React Frontend  →  POST /api/generate-protocol
  • Hybrid Search   →  BM25 + ChromaDB (langchain EnsembleRetriever)
  • LLM Generator   →  Groq (llama-3.3-70b-versatile) via LangChain

Run with:
    uvicorn app.api:app --reload --port 8000
"""

import os
import sys
import json
import hashlib

# ── path bootstrap so "src" package is always importable ─────────────────────
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dotenv import load_dotenv
load_dotenv()
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional

from langchain_groq import ChatGroq
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

from src.llm_engine import load_index, get_hybrid_retriever
from src.config import VECTOR_STORE_DIR

# ── FastAPI app setup ─────────────────────────────────────────────────────────
app = FastAPI(
    title="CDSS — Precision Oncology API",
    description="RAG-powered Clinical Decision Support System backend",
    version="1.0.0",
)

# Allow all origins for local React development (tighten in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global retriever and cache ───────────────────────────────────────────
_retriever = None
response_cache = {}


@app.on_event("startup")
def load_retriever():
    """Load ChromaDB index and build the Hybrid Retriever on startup."""
    global _retriever
    vector_store_path = str(VECTOR_STORE_DIR)
    if os.path.exists(vector_store_path) and os.listdir(vector_store_path):
        vectorstore = load_index()
        _retriever = get_hybrid_retriever(vectorstore, k=5)
        print("[OK] Hybrid retriever ready.")
    else:
        print("[WARNING] Vector store not found. Run the ingestion pipeline first.")


# ── Pydantic input / output models ───────────────────────────────────────────
class PatientProfile(BaseModel):
    tumor_type: str = Field(..., example="Non-Small Cell Lung Cancer")
    biomarkers: List[str] = Field(default=[], example=["EGFR exon 19 deletion"])
    egfr: Optional[int] = Field(None, example=45, description="eGFR in mL/min/1.73m²")
    alt_ast: Optional[int] = Field(None, example=60, description="ALT/AST level in U/L")
    ecog_status: Optional[str] = Field(None, example="1 - Restricted in strenuous activity", description="ECOG Performance Status")
    comorbidities: List[str] = Field(default=[], example=["Chronic Kidney Disease", "Hypertension"])


class ProtocolResponse(BaseModel):
    protocol: dict
    safety_alerts: dict
    alternatives: str = "No alternatives specified."
    citations: str = "No citations provided."
    clinical_rationale: str = "Clinical rationale could not be generated completely. Please review the patient's critical performance status (ECOG 3/4) which typically indicates Best Supportive Care."


# ── Retrieval helper (swap this with your full LangChain logic) ───────────────
def retrieve_medical_chunks(query: str) -> List[str]:
    """
    Retrieves relevant medical text chunks from ChromaDB via the Hybrid Retriever.
    Returns dummy chunks if the retriever is not initialised (dev/test mode).
    """
    if _retriever is None:
        # Placeholder dummy data — replace with real retriever when index is ready
        return [
            "NCCN Guidelines recommend osimertinib as first-line therapy for EGFR-mutant NSCLC.",
            "Dose adjustment may be required for patients with severe renal impairment (eGFR < 30).",
            "PD-L1 inhibitors are contraindicated in patients with active autoimmune disease.",
        ]

    docs = _retriever.invoke(query)
    return [
        f"[{doc.metadata.get('document_name', 'Unknown')}, "
        f"Page {doc.metadata.get('page_number', '?')}]\n{doc.page_content}"
        for doc in docs
    ]


# ── LLM + Prompt setup ───────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert Clinical Decision Support AI for Precision Oncology.
Analyze the patient profile and the retrieved clinical context below.

You MUST return ONLY a valid JSON object with this EXACT structure — no markdown, no extra text:
{{
  "protocol": {{
    "treatment": "Specific treatment recommendation with dosage",
    "confidence": "high | medium | low",
    "monitoring": "Required monitoring parameters and schedule"
  }},
  "safety_alerts": {{
    "alert_text": "Critical safety warning relevant to this patient",
    "severity": "critical | warning | info"
  }},
  "alternatives": "Alternative treatment options if first-line is contraindicated",
  "citations": "Guideline source and page numbers used (e.g. NCCN NSCLC v7.2026, p.165)",
  "clinical_rationale": "Detailed step-by-step medical reasoning linking patient data to the recommendation"
}}

RULES:
1. Base ALL claims ONLY on the provided context. Never use outside medical knowledge.
2. If the context is insufficient, set confidence to "low" and explain why in clinical_rationale.
3. Never invent citations. Never soften a refusal into a partial guess.
4. Highlight renal/hepatic dose adjustments if eGFR or ALT/AST values are provided.

DYNAMIC CONFIDENCE SCORING:
Determine the Confidence Level based strictly on the quality and explicit warnings in the retrieved guidelines:
- HIGH: The retrieved context explicitly supports the treatment for the patient's full profile without any warnings or precautions regarding their specific comorbidities.
- LOW: The retrieved context explicitly mentions risks, cautions, or requires multidisciplinary review for the patient's specific comorbidities, OR the context lacks sufficient data regarding their specific secondary conditions.

CRITICAL: If the retrieved medical guidelines suggest multiple valid and equally preferred treatment options for the patient's condition, ALWAYS select the FIRST option explicitly mentioned in the retrieved context. Do not vary your answer for the same input, and do not default to any specific medication unless explicitly supported by the context."""

HUMAN_TEMPLATE = """--- Retrieved Clinical Context ---
{context}

--- Patient Profile ---
Tumor Type: {tumor_type}
Biomarkers: {biomarkers}
ECOG Status: {ecog_status}
eGFR: {egfr}
ALT/AST: {alt_ast}
Comorbidities: {comorbidities}

Generate the JSON protocol now."""

prompt = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", HUMAN_TEMPLATE),
])

llm = ChatGroq(
    model_name="openai/gpt-oss-20b",
    temperature=0,
    max_tokens=2048,
    model_kwargs={"response_format": {"type": "json_object"}}
)

# Chain: Prompt → LLM → JSON Parser
chain = prompt | llm | JsonOutputParser()


# ── Main RAG endpoint ─────────────────────────────────────────────────────────
@app.post("/api/generate-protocol", response_model=ProtocolResponse)
async def generate_protocol(patient: PatientProfile):
    """
    Main RAG orchestration endpoint.
    1. Build a search query from the patient profile.
    2. Retrieve relevant medical chunks via Hybrid Search.
    3. Run the LLM chain to generate a grounded JSON protocol.
    """
    # Cache Check
    request_data_str = json.dumps(patient.model_dump(), sort_keys=True)
    cache_key = hashlib.md5(request_data_str.encode('utf-8')).hexdigest()
    
    if cache_key in response_cache:
        print(f"[CACHE HIT] Returning cached protocol for key: {cache_key}")
        return response_cache[cache_key]

    try:
        # Step A — Build search query from patient data
        biomarker_str = ", ".join(patient.biomarkers) if patient.biomarkers else "unknown"
        comorbidity_str = ", ".join(patient.comorbidities) if patient.comorbidities else "none"
        query = (
            f"{patient.tumor_type} with {biomarker_str} "
            f"treatment guidelines comorbidities: {comorbidity_str}"
        )

        # Step B — Retrieve medical chunks
        chunks: List[str] = retrieve_medical_chunks(query)
        
        if not chunks:
            # Fallback if the strict 0.75 similarity threshold returns no chunks
            fallback_response = ProtocolResponse(
                protocol={
                    "treatment": "No recommendation possible. Retrieved context did not meet the strict 0.75 similarity threshold.",
                    "confidence": "low",
                    "monitoring": "Requires multidisciplinary clinical review."
                },
                safety_alerts={
                    "alert_text": "Insufficient data in retrieved guidelines to form a safe protocol for this specific patient profile.",
                    "severity": "critical"
                },
                alternatives="N/A",
                citations="N/A",
                clinical_rationale="The semantic search retriever found no relevant medical guidelines matching the 0.75 similarity threshold for this query. The AI is restricted from hallucinating outside the provided context."
            )
            response_cache[cache_key] = fallback_response
            return fallback_response

        context = "\n\n---\n\n".join(chunks)

        # Step C — Generate grounded response via LLM chain
        result: dict = chain.invoke({
            "context": context,
            "tumor_type": patient.tumor_type,
            "biomarkers": biomarker_str,
            "ecog_status": patient.ecog_status if patient.ecog_status else "Not provided",
            "egfr": patient.egfr if patient.egfr is not None else "Not provided",
            "alt_ast": patient.alt_ast if patient.alt_ast is not None else "Not provided",
            "comorbidities": comorbidity_str,
        })

        protocol_response = ProtocolResponse(**result)
        response_cache[cache_key] = protocol_response
        return protocol_response

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=500,
            detail=f"LLM returned malformed JSON. Parser error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during protocol generation: {str(e)}"
        )


# ── Health check endpoint ─────────────────────────────────────────────────────
@app.get("/health")
def health_check():
    """Simple liveness probe for the frontend to verify the API is running."""
    return {
        "status": "ok",
        "retriever_ready": _retriever is not None,
    }

# ── Cache Management ──────────────────────────────────────────────────────────
@app.post("/api/clear-cache")
async def clear_cache():
    """Endpoint to invalidate the in-memory cache."""
    response_cache.clear()
    return {"status": "ok", "message": "Cache cleared successfully"}
