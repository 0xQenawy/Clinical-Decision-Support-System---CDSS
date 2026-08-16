from pathlib import Path

# Project root is assumed to be one level up from the src directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Vector store directory
VECTOR_STORE_DIR = PROJECT_ROOT / "vector_store"

# Text splitter configuration
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
