import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from loguru import logger

from config import DATA_PATH, CHUNK_SEPARATOR, WORD_SEPARATOR, debug
from utils.string import extract_text_from_pdf_per_page, extract_words_sentences


def process_pdf(pdf: Path, company: str):
    logger.warning(f"Processing {pdf}...")

    data_path = pdf.parent / pdf.stem
    data_path.mkdir(exist_ok=True)

    pages = extract_text_from_pdf_per_page(pdf)
    total_pages = len(pages)

    metadata_path = data_path / f"metadata.json"
    metadata = {
        "name": pdf.stem,
        "company": company,
        "pages": total_pages,
    }
    metadata_path.write_text(json.dumps(metadata, indent=4), encoding="utf-8")

    for index, page_text in enumerate(pages, start=1):
        logger.info(f"Processing page {index}/{total_pages}...")

        txt_path = data_path / f"{index}.txt"
        txt_path.write_text(page_text, encoding="utf-8")

        words, sentences = extract_words_sentences(page_text)

        words_path = data_path / f"{index}_words.txt"
        words_path.write_text(WORD_SEPARATOR.join(words), encoding="utf-8")

        sentences_path = data_path / f"{index}_sentences.txt"
        sentences_path.write_text(CHUNK_SEPARATOR.join(sentences), encoding="utf-8")


if __name__ == "__main__":
    logger.debug(debug())

    with ThreadPoolExecutor() as executor:
        dataset = pd.read_csv(Path(__file__).parent / "dataset.csv")
        for pdf in DATA_PATH.glob("*.pdf"):
            try:
                company = dataset[dataset["sha1"] == pdf.stem]["name"].values[0]
                executor.submit(process_pdf, pdf, company)
            except IndexError:
                logger.error(f"Cannot find company name for {pdf}")
