# RAG via local model

The implementation relies on `openchat/openchat-3.5-0106` model from Hugging Face's library. The goal is to extract the `query similarity ratio` of each sentence using Sci-kit Learn's `cosine_similarity` metric. A vector database is then created per document with all the pre-selected chunks. Later on, only the `N` most relevant sentences are extracted from the database. The final step is to select the top `M` most relevant documents after sorting them by the `sentence availability ratio`.

## Steps

1. `Pre-process`: extracting & cleaning all words and sentences, storing them into separate files.
2. `Pre-filter`: for each question and document, extract the most `N` relevant chunks based on the `cosine_similarity` metric and a `query similarity ratio` threshold.
3. `Post-filter`: for each question, select the `M` most relevant documents based on the `sentence availability ratio`.
4. `LLM`: request the agent for the answer based on the selected documents.

## Running

1. `pip install -r requirements.txt`
2. (optional) Install PyTorch with CUDA support: `pip install torch --index-url https://download.pytorch.org/whl/cu122`
3. Copy all the relevant PDFs and questions to the `data` folder.
4. Run `python preprocess.py` to pre-process the documents. All the pre-processed files will be stored in a `data/PDF_NAME` folder.
5. Run `python rag.py`. Answers and the config used will be stored in `data/answers.json` and `data/answers_config` files.

## Known Issues/Future Improvements

1. Pre-processing is too slow still. Needs optimization and parallelization.
2. Question answering also needs optimization and parallelization (e.g. batch processing).
3. Better performant models (e.g. meta-llama/Meta-Llama-3.1-405B-Instruct) are tricky to use because of GPU memory constraints.
4. Table extraction is poorly implemented. Improving the Markdown tables extraction could be a win!
5. Using sub-agent to pre-process and pre-filter documents could be a win!
6. HuggingFace's pipeline has several parameters that could be tuned (e.g. quantization, accelerators, precision, batch processing).
7. and many more...

*NOTE: code is not even nearly optimized and lack of comments. It was a dirty implementation to test the idea. The results were gathared using Google Colab with a 53.0 GB + L4 24GB GPU VM*
