# Daniel's Approach

## Overview

This directory contains [@danielweller-swp](https://www.github.com/danielweller-swp)'s solution to the [enterprise-rag-challenge](https://github.com/trustbit/enterprise-rag-challenge/).

## Architecture

To solve the challenge, i.e. to answer questions about companies given some PDFs describing the companies, we
use the following approach:

### Create a knowledge database from each PDF

Using GPT-4o, analyse as large chunks of the given PDFs as possible
(usually, the whole PDF fits into the context window). The result of this analysis is a "knowledge database" containing metrics extracted from the PDF. The metrics, like "operating margin" and "market capitalization",
are pre-defined based on the information from the `enterprise-rag-challenge`.

See the directory [output](./output/) for an example set of knowledge databases.

### Answer questions using the knowledge databases

Given a question, we forward the question to GPT-4o, alongside all the previously extracted knowledge databases. See [results.json](./results.json) for an example set of questions & answers
based on the example set of knowledge databases.

### Notes

Ingesting a new PDF, or changing the metrics and therefore re-ingesting the PDFs, is the most expensive step.
Answering a question for a fixed set of PDFs and metrics is cheap. So this solution is cheapest if questions 
are asked often, but the PDFs / metrics change rarely.

## Running

Create a `.env` file containing an OpenAI API key. Example:

```
OPENAI_API_KEY=sk-proj-thisisafakeapikey
```

Install requirements.
```
pip install -r requirements.txt
```

Put the relevant PDFs as well as the `questions.json` file (from the challenge) into the `samples` directory,
and the file `dataset.csv` from the [enterprise-rag-challenge](https://github.com/trustbit/enterprise-rag-challenge/) repo into this directory.

Then, execute the `create_knowledge_base.ipynb` notebook to generate the knowledge base that will appear in
the `output` directory.

Finally, run the `answer_question.ipynb` notebook to answer the questions from `questions.json`. The results
will be stored in `results.json`.