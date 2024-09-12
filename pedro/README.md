# RAG via local model

The implementation relies on the `openchat/openchat-3.5-0106` model from the Hugging Face's library. The goal is to extract the `query similarity ratio` of each sentence using Sci-kit Learn's `cosine_similarity` metric. A vector database is then created per document with all the pre-selected chunks. Later on, only the `N` most relevant sentences are extracted from the database. The final step is to select the top `M` most relevant documents after sorting them by the `sentence availability ratio`.

## Steps

1. `Pre-process`: extracting & cleaning all words and sentences, storing them into separate files.
2. `Pre-filter`: for each question and document, extract the most `N` relevant chunks based on the `cosine_similarity` metric and a `query similarity ratio` threshold.
3. `Post-filter`: for each question, select the `M` most relevant documents based on the `sentence availability ratio`.
4. `LLM`: request the agent for the answer based on the selected documents.

## Running

1. `pip install -r requirements.txt`
2. Copy all the relevant PDFs and questions to the `data` folder.
3. Run `python preprocess.py` to pre-process the documents. All the pre-processed files will be stored in the `data/PDF_NAME` folder.
4. Run `python rag.py`. Answers will be stored in `answers.json` file.

## Known Issues/Future Improvements

1. Pre-processing is still too slow. Needs optimization and parallelization.
2. Because of GPU and space constraints, can not use a better model (e.g. meta-llama/Meta-Llama-3.1-405B-Instruct)
3. Again, because of GPU memory, can not use a larger `N` values or bigger chunks for the pre-filtering step for evaluation. The downside of that approach is end up confusing the model with too many chunks.
4. Table structure is poorly implemented. Maybe Markdown tables would be a better choice.
5. Using "pymupdf4llm" library to extract Markdown content from PDFs could be a win!
6. While using Markdown text, chunks split by paragraphs/headers could be a win!
7. Using sub-agent to pre-process and pre-filter documents could be a win!
8. HuggingFace's pipeline has lots of parameters that could be tuned (e.g. quantization, accelerators, precision).
9. and many more...

*NOTE: code is not even nearly optimized and lack of comments. It was a dirty implementation to test the idea. The results were gathared using Google Colab with a 53.0 GB + L4 24GB GPU VM*
