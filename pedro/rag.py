import gc
import json

import pandas as pd
import tiktoken
import torch
from loguru import logger

from config import (
    DATA_PATH,
    MAX_DOCUMENTS_TO_LLM_CONTEXT,
    MAX_CHUNK_TO_USE,
    MIN_CHUNK_AVAILABILITY_CUTOFF_THRESHOLD,
    ROOT_PATH,
    CHUNK_SEPARATOR,
    WORD_SEPARATOR,
    debug
)
from utils.llm import ask_question
from utils.string import (
    extract_relevant_sentences,
    filter_relevant_chunks,
    generate_faiss_index,
)

debug(print_config=True)

gc.collect()
torch.cuda.empty_cache()

QUESTIONS = pd.read_json(DATA_PATH / "questions.json")
ANSWERS = DATA_PATH / "answers.json"
ANSWERS_CONFIG = DATA_PATH / "answers_config.json"
QUESTION_PROMPT = (ROOT_PATH / "prompt_question.txt").read_text()

answers = []
for _, row in QUESTIONS.iterrows():
    question = row["question"]
    question_schema = row["schema"]
    logger.warning(f'Question "{question}"...')

    pdf_directories = [
        path
        for path in DATA_PATH.iterdir()
        if path.is_dir() and (path / "metadata.json").exists()
    ]
    documents = []
    for pdf_directory in pdf_directories:
        metadata = json.loads((pdf_directory / "metadata.json").read_text())
        company = metadata["company"]

        relevant_sentences = []
        total_sentences = 0
        for page in range(1, metadata["pages"] + 1):
            words = (
                (pdf_directory / f"{page}_words.txt")
                .read_text(encoding="utf-8")
                .split(WORD_SEPARATOR)
            )
            sentences = (
                (pdf_directory / f"{page}_sentences.txt")
                .read_text(encoding="utf-8")
                .split(CHUNK_SEPARATOR)
            )

            total_sentences += len(sentences)
            relevant_sentences += extract_relevant_sentences(question, sentences, words)

        total_relevant_sentences = len(relevant_sentences)
        sentence_availability_ratio = total_relevant_sentences / total_sentences

        # extra weight to the document if the company name matches the question
        if company in question:
            sentence_availability_ratio += MIN_CHUNK_AVAILABILITY_CUTOFF_THRESHOLD

        sentence_availability_ratio = min(sentence_availability_ratio, 100)
        sentence_availability_pct = round(sentence_availability_ratio * 100, 2)
        logger.info(
            f"Found {total_relevant_sentences}/{total_sentences} (%{sentence_availability_pct}) relevant sentences for {pdf_directory.stem}, {company}..."
        )

        if relevant_sentences and sentence_availability_ratio >= MIN_CHUNK_AVAILABILITY_CUTOFF_THRESHOLD:
            index = generate_faiss_index(relevant_sentences)
            relevant_chunks = filter_relevant_chunks(
                index, relevant_sentences, question, vector_size=MAX_CHUNK_TO_USE
            )
            documents.append(
                {
                    "metadata": metadata,
                    "sentences": relevant_chunks,
                    "sentence_availability_pct": sentence_availability_pct,
                }
            )

    if not documents:
        logger.error("No relevant documents found for the question!")
        answers.append(
            {
                "question": question,
                "schema": question_schema,
                "answer": "N/A",
            }
        )
        continue

    # sort the documents based on the similarity score and pick the top N documents
    sorted_documents = sorted(
        documents, key=lambda x: x["sentence_availability_pct"], reverse=True
    )
    top_n_documents = sorted_documents[:MAX_DOCUMENTS_TO_LLM_CONTEXT]

    all_filtered_metadata = []
    context = ""
    for index, document in enumerate(top_n_documents, start=1):
        metadata = document["metadata"]
        sentence_availability_pct = document["sentence_availability_pct"]
        sentences = document["sentences"]
        company = metadata["company"]

        text = CHUNK_SEPARATOR.join(sentences)

        context += f"""
        DOCUMENT #{index}, COMPANY \"{company}\":
        {text}
        ---
        """

        all_filtered_metadata.append(metadata)

    question_context = f"""
    The DOCUMENTS are listed is below.
    ---------------------
    {context}
    ---------------------
    Given the DOCUMENTS provided, answer the QUESTION using a '{question_schema}' schema.
    Question: {question}
    Answer:
    """

    encoding = tiktoken.get_encoding("cl100k_base")
    tokens = encoding.encode(question_context)
    logger.debug(f"Tokens: {len(tokens)}, Documents: {all_filtered_metadata}...")

    try:
        answer = ask_question(QUESTION_PROMPT, question_context)
        logger.success(f"Answer: {answer}")
    except Exception as e:
        answer = "N/A"
        logger.error(f"Error: {e}...")

    answers.append(
        {
            "question": question,
            "schema": question_schema,
            "answer": answer,
        }
    )

json.dump(debug(), open(ANSWERS_CONFIG, "w"), indent=4)
json.dump(answers, open(ANSWERS, "w"), indent=4)
