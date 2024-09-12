import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pandas as pd
from loguru import logger

from config import DATA_PATH, WORD_SEPARATOR, debug
from utils.string import extract_sentences_from_pdf, extract_words


def process_pdf(pdf: Path, company: str):
    logger.warning(f"Processing {pdf}...")

    data_path = pdf.parent / pdf.stem
    data_path.mkdir(exist_ok=True)

    sentences = extract_sentences_from_pdf(pdf)
    total_sentences = len(sentences)

    metadata_path = data_path / f"metadata.json"
    metadata = {
        "name": pdf.stem,
        "company": company,
        "sentences": total_sentences,
    }
    metadata_path.write_text(json.dumps(metadata, indent=4), encoding="utf-8")

    txt_path = data_path / f"{pdf.stem}.txt"
    txt_path.write_text("\n".join(sentences), encoding="utf-8")

    for index, sentence in enumerate(sentences, start=1):
        logger.info(f"Processing sentence {index}/{total_sentences}...")

        words = extract_words(sentence)
        words_path = data_path / f"{index}_words.txt"
        words_path.write_text(WORD_SEPARATOR.join(words), encoding="utf-8")

        sentence_path = data_path / f"{index}.txt"
        sentence_path.write_text(sentence, encoding="utf-8")


if __name__ == "__main__":
    logger.debug(debug())

    # process_pdf(Path("data_sample/9ae3bb21564a5098c4b4d6450655c22eff85deae.pdf"), "Strike Energy Limited")

    with ThreadPoolExecutor(max_workers=4) as executor:
        dataset = pd.read_csv(Path(__file__).parent / "dataset.csv")
        for pdf in DATA_PATH.glob("*.pdf"):
            try:
                company = dataset[dataset["sha1"] == pdf.stem]["name"].values[0]
                executor.submit(process_pdf, pdf, company)
            except IndexError:
                logger.error(f"Cannot find company name for {pdf}")
