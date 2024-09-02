from typing import Tuple

import torch
from transformers import pipeline

from config import DEVICE, HUGGINGFACE_API_KEY, LLM_MODEL

LLM_PIPELINE = pipeline(
    "text-generation",
    model=LLM_MODEL,
    device=DEVICE,
    torch_dtype=torch.float16,  # otherwise it will run out of memory
    token=HUGGINGFACE_API_KEY,
)
LLM_PIPELINE_ARGS = {
    "max_new_tokens": 1024,
    "return_full_text": False,
    "do_sample": False,
}


def ask_question(prompt: str, question: str) -> Tuple[str, str]:
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]

    output = LLM_PIPELINE(messages, **LLM_PIPELINE_ARGS)
    answer = output[0]["generated_text"].strip()

    return answer
