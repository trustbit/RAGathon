import os
from pathlib import Path
import torch
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")

ROOT_PATH = Path(__file__).parent
DATA_PATH = ROOT_PATH / "data"

WORD_SEPARATOR = "\n"
CHUNK_SEPARATOR = "\n\n"

CHUNK_SIZE = 1000 # 1000
CHUNK_SIMILARITY_CUTOFF_THRESHOLD = 0.05
CHUNK_TRANSFORMER_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

MIN_CHUNK_AVAILABILITY_CUTOFF_THRESHOLD = 0.35
MAX_CHUNK_TO_USE = 8
MAX_DOCUMENTS_TO_LLM_CONTEXT = 3

#LLM_MODEL = "microsoft/Phi-3-mini-128k-instruct"
#LLM_MODEL = "microsoft/Phi-3.5-mini-instruct"
#LLM_MODEL = "meta-llama/Meta-Llama-3.1-8B-Instruct"
LLM_MODEL = "openchat/openchat-3.5-0106"

def debug(print_config: bool = False) -> dict:
  config_data = {
    "DEVICE": str(DEVICE),
    "DATA_PATH": str(DATA_PATH),
    "WORD_SEPARATOR": repr(WORD_SEPARATOR),
    "CHUNK_SEPARATOR": repr(CHUNK_SEPARATOR),
    "CHUNK_SIZE": CHUNK_SIZE,
    "CHUNK_SIMILARITY_CUTOFF_THRESHOLD": CHUNK_SIMILARITY_CUTOFF_THRESHOLD,
    "CHUNK_TRANSFORMER_MODEL": CHUNK_TRANSFORMER_MODEL,
    "MIN_CHUNK_AVAILABILITY_CUTOFF_THRESHOLD": MIN_CHUNK_AVAILABILITY_CUTOFF_THRESHOLD,
    "MAX_CHUNK_TO_USE": MAX_CHUNK_TO_USE,
    "MAX_DOCUMENTS_TO_LLM_CONTEXT": MAX_DOCUMENTS_TO_LLM_CONTEXT,
    "LLM_MODEL": LLM_MODEL,
  }

  if print_config:
    for key, value in config_data.items():
      logger.debug(f"{key} = {value}")

  return config_data
