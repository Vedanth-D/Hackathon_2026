"""Application configuration."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATASET_DIR = Path(os.getenv("DATASET_DIR", PROJECT_ROOT / "dataset"))
OUTPUT_PATH = Path(os.getenv("OUTPUT_PATH", PROJECT_ROOT / "output.csv"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", PROJECT_ROOT / ".cache"))

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4o-mini")

MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUESTS_PER_MINUTE = int(os.getenv("REQUESTS_PER_MINUTE", "30"))

# Pricing assumptions (USD per 1M tokens) for operational analysis
PRICING = {
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4o": {"input": 2.50, "output": 10.00},
}

CACHE_DIR.mkdir(parents=True, exist_ok=True)
