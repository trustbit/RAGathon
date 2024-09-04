# RAG experiments

This repository documents my initial experiments with RAG using OpenAI's API. My goal was to evaluate how well would an OpenAI [Assistant](https://platform.openai.com/docs/assistants/overview) with its capability to [process attached files](https://platform.openai.com/docs/assistants/deep-dive/creating-assistants) and equiped with one of the most advanced models **gpt-4o** handle the problem out of the box. Below are the details of the different approaches I tested.


## Experiment 1: Passing merged PDF file to a single Thread
In the first experiment, I attempted to combine all PDF files into a single document, pass it to a thread in the Assistant, and then send messages with the questions to this single thread. The approach is implemented in `answer_questions_all_files_merged.py`.

**Results:**
* **Outcome**: The approach worked, but GPT-4o exhibited significant hallucination.
* **Cost**: Answering 40 questions cost ~ $4 (~800K tokens).

## Experiment 2: Passing PDF files separately to a single Thread
In the second experiment, the idea was to provide the company name together with each file and make gpt use only relevant files. The implementation can be found in `answer_questions_all_files_separately.py`. 

I didn't find a way to pass file metadata in a way that makes it visible to gpt, so I simply renamed the pdf files using company name as a file name (read more about extracting company names below). Regardless of the naming part, I bumped into the limit of 10 files per thread, and thus swiched to Experiment 3. 

## Experiment 3: Passing only relevant PDF files, one thread per question
The third experiment involved creating a separate thread for each question and passing only the relevant one or two files to it. This approach is implemented in `answer_questions_filtered_source_threads.py`.

In order to find relevant files, I extracted company names from them. I first took 1 or 2 first pages of each pdf and created a thread with the request to extract the company name (`extract_names_from_pdfs.py`). Here I learned that assistants don't tackle images in pdfs (e.g. logos). So I converted the first 1 or 2 pages to images, did OCR and passed the text to a thread (`extract_names_from_text.py`). 

The outcomes of 4 different approaches can be found in `analysis/names`. They are based on the PDFs from Samples. One can see that passing PDFs is clearly cheaper than passing the text from them, and that adding the second page doesn't double the cost. It's also obvious, that the OCR method with 2 pages performed the best, with a total cost of only $0.07.

**Results:**
* **Outcome**: This approach provided slighlty better answers than using the merged file. It would be interesting to test it on a set of questions with a smaller chunk of n/a answers.
* **Cost**: Answering 40 questions cost on average ~$5 (~1M tokens).

## Experiment 4: Structured outputs with Instructor 

In the last experiment, I tried using Instructor, a wrapper for various LLM APIs that provides AI-generated answers in a structured JSON format, as defined by a pydantic model. More details are available at [Instructor blog](https://python.useinstructor.com/blog/2024/06/15/zero-cost-abstractions/). The implementation can be found in `answer_questions_filtered_source_instructor.py`. 

Unfortunately, Instructor works with OpenAI Completions only, which don't support file attachments. The attempt of reading PDFs and passing text failed due to the 120000 input token limit for completions.

And here I ran out of time.


# Technical details

## Running

Create a `.env` file containing an OpenAI API key. Example:

```
OPENAI_API_KEY_RAG_CHALLENGE=sk-proj-thisisafakeapikey
```

Install requirements.
```
pip install -r requirements.txt
```

**OCR dependencies:**

The pdf2image library relies on an external tool called Poppler to process PDF files.

```
brew install poppler
sudo apt-get install poppler-utils
```

The pytesseract library relies on the OCR engine call Tesseract to recognize images.

```
brew install tesseract
sudo apt-get install tesseract-ocr
```

Put the relevant PDFs as well as the `questions.json` file (from the challenge) into the `data/samples` directory, then run scripts.
