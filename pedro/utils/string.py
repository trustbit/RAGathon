import re
import warnings
from pathlib import Path
from typing import List, Set, Tuple

import faiss
import fitz
import torch
from langchain.docstore.document import Document as LangchainDocument
from langchain.text_splitter import RecursiveCharacterTextSplitter
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import AutoModel, AutoTokenizer

from config import (
    CHUNK_SIZE,
    CHUNK_SIMILARITY_CUTOFF_THRESHOLD,
    CHUNK_TRANSFORMER_MODEL,
    MAX_CHUNK_TO_USE
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


def clean_text(text):
    # Remove URLs
    text = re.sub(r"http\S+|www\S+|https\S+", "", text, flags=re.MULTILINE)
    # Remove HTML tags
    text = re.sub(r"<.*?>", "", text)
    # Remove non-alphabetic characters (optional, depending on the use case)
    text = re.sub(r"[^a-zA-Z0-9\s]", "", text)
    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_text_from_pdf_per_page(path: Path) -> List[str]:
    pdf = fitz.open(path)
    pages = []
    for page_number in range(pdf.page_count):
        page = pdf.load_page(page_number)
        pages.append(page.get_text())

    return pages


def extract_words_sentences(text: str) -> Tuple[Set[str], Set[str]]:
    document = LangchainDocument(page_content=text)
    sentences = [
        sentence.page_content for sentence in TEXT_SPLITTER.split_documents([document])
    ]

    words = {word.lower() for word in word_tokenize(text)}
    words = {word for word in words if word not in NLKT_STOPWORDS and word.isalpha()}

    words_extanded = [
        ABBREVIATION_DICT_LOWERCASE.get(word, word).lower() for word in words
    ]
    words_extanded = word_tokenize(" ".join(words_extanded))
    words = words.union(words_extanded)

    return words, sentences


def combine_sentences(sentences: list, buffer_size=1) -> list:
    sentences = [
        {"sentence": x.page_content, "index": i} for i, x in enumerate(sentences)
    ]
    combined_sentences = []
    for i in range(len(sentences)):
        combined_sentence = " "
        for j in range(i - buffer_size, i):
            if j >= 0:
                combined_sentence += sentences[j]["sentence"] + " "

        combined_sentence += sentences[i]["sentence"]

        for j in range(i + 1, i + 1 + buffer_size):
            if j < len(sentences):
                combined_sentence += " " + sentences[j]["sentence"]

        combined_sentences.append(combined_sentence)

    return combined_sentences


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


def extract_relevant_sentences(
    question: str,
    sentences: list,
    words: list,
    similarity_threshold: float = CHUNK_SIMILARITY_CUTOFF_THRESHOLD,
) -> list:
    if not question or not sentences or not words:
        return []

    vectorizer = TfidfVectorizer(stop_words="english")

    question_words, _ = extract_words_sentences(question)

    try:
        words_vector = vectorizer.fit_transform(words)
    except ValueError:
        return []

    question_vector = vectorizer.transform(question_words)
    scores = cosine_similarity(words_vector, question_vector).flatten()

    if not any(scores == 1): # not matching words found, bad sign!
        return []

    try:
        sentences_vector = vectorizer.fit_transform(
            [sentence.lower() for sentence in sentences]
        )
    except ValueError:
        return []

    question_vector = vectorizer.transform(question_words)
    scores = cosine_similarity(sentences_vector, question_vector)

    relevant_sentences = []
    for index, score in enumerate(scores):
        avg_score = sum(score)/len(score > 0)
        if avg_score >= similarity_threshold:
            relevant_sentences.append(sentences[index])

    return relevant_sentences

