import re
from typing import Any

import torch
from transformers import BitsAndBytesConfig, pipeline

from config import HUGGINGFACE_API_KEY, LLM_MODEL

LLM_PIPELINE = pipeline(
    "text-generation",
    model=LLM_MODEL,
    device_map="auto",
    token=HUGGINGFACE_API_KEY,
    model_kwargs={
        "torch_dtype": torch.float16,
        "quantization_config": BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_compute_dtype=torch.float16
        ),
        "use_safetensors": True,
        "output_attentions": False,
        "output_hidden_states": False,
    },  # some configs has to be passed directly to the model
    num_beams=1,
    early_stopping=False,  # num_beams is already = 1, so nothing to stop from
    do_sample=False,
    padding=True,
)
LLM_PIPELINE_ARGS = {
    "max_new_tokens": 1024,
    "return_full_text": False,
}
LLM_PIPELINE.tokenizer.pad_token_id = LLM_PIPELINE.model.config.eos_token_id


def ask_question(prompt: str, question: str, schema: str) -> Any:
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": question},
    ]

    output = LLM_PIPELINE(messages, **LLM_PIPELINE_ARGS)
    answer = output[0]["generated_text"].strip()

    if schema == "number":
        try:
            answer = float(re.sub(r"[^\d.]", "", answer))
        except ValueError:
            answer = "N/A"

    return answer
