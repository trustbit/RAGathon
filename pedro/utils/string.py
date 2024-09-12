import warnings
from pathlib import Path
from typing import List, Set

import faiss
import pymupdf4llm
import torch
from langchain.text_splitter import RecursiveCharacterTextSplitter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoTokenizer

from config import (
    CHUNK_SIMILARITY_CUTOFF_THRESHOLD,
    CHUNK_SIZE,
    CHUNK_TRANSFORMER_MODEL,
    MAX_CHUNK_TO_USE,
)
from utils.abbreviations import ABBREVIATION_DICT_LOWERCASE

warnings.filterwarnings("ignore", module="transformers")

TEXT_TOKENIZER = AutoTokenizer.from_pretrained(CHUNK_TRANSFORMER_MODEL)
TEXT_TOKENIZER_MODEL = AutoModel.from_pretrained(CHUNK_TRANSFORMER_MODEL)

TEXT_SPLITTER = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
    tokenizer=TEXT_TOKENIZER,
    chunk_size=CHUNK_SIZE,
    chunk_overlap=(CHUNK_SIZE // 10),
    strip_whitespace=True,
)

NLKT_STOPWORDS = set(stopwords.words("english"))


def extract_sentences_from_pdf(path: Path) -> List[str]:
    text = pymupdf4llm.to_markdown(path, pages=None, write_images=False)
    sentences = TEXT_SPLITTER.split_text(text)

    return sentences


def extract_words(text: str) -> Set[str]:
    words = {word.lower() for word in word_tokenize(text)}
    words = {word for word in words if word not in NLKT_STOPWORDS and word.isalpha()}

    words_extended = [
        ABBREVIATION_DICT_LOWERCASE.get(word, word).lower() for word in words
    ]
    words_extended = word_tokenize(" ".join(words_extended))
    words = words.union(words_extended)

    return words


def tokenizer_mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = (
        attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    )
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(
        input_mask_expanded.sum(1), min=1e-9
    )


def generate_faiss_index(chunks: list) -> faiss.IndexFlatL2:
    tokens = TEXT_TOKENIZER(chunks, padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        model_output = TEXT_TOKENIZER_MODEL(**tokens)
        embbedings = tokenizer_mean_pooling(model_output, tokens["attention_mask"])
    index = faiss.IndexFlatL2(embbedings.shape[1])
    index.add(embbedings)
    return index


def filter_relevant_chunks(
    index: faiss.IndexFlatL2,
    chunks: list,
    query: str,
    vector_size: int = MAX_CHUNK_TO_USE,
) -> list[str]:
    tokens = TEXT_TOKENIZER([query], padding=True, truncation=True, return_tensors="pt")
    with torch.no_grad():
        model_output = TEXT_TOKENIZER_MODEL(**tokens)
        embbedings = tokenizer_mean_pooling(model_output, tokens["attention_mask"])
    _, I = index.search(embbedings, vector_size)
    return [chunks[i] for i in I[0]]


def is_sentence_relevant(
    question: str,
    sentence: str,
    words: list,
    similarity_threshold: float = CHUNK_SIMILARITY_CUTOFF_THRESHOLD,
) -> bool:
    if not question or not sentence or not words:
        return False

    vectorizer = TfidfVectorizer(stop_words="english")

    question_words = extract_words(question)

    try:
        words_vector = vectorizer.fit_transform(words)
    except ValueError:
        return False

    question_vector = vectorizer.transform(question_words)
    scores = cosine_similarity(words_vector, question_vector).flatten()

    if not any(scores == 1):  # not matching words found, bad sign!
        return False

    try:
        sentences_vector = vectorizer.fit_transform([sentence.lower()])
    except ValueError:
        return False

    question_vector = vectorizer.transform(question_words)
    scores = cosine_similarity(sentences_vector, question_vector)

    if sum(scores[0]) / len(scores[0] > 0) >= similarity_threshold:
        return True

    return False
