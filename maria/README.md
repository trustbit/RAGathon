# Question answering

Work In Progress

## Approach 1. Combine all PDF files in one

Then ask all question in one thread. The merged file is provided once.

## Approach 2. Extract company names and provide only relevant PDF files

Ask each question in a separate thread.

### Name extraction

#### Idea 1. Assistant reads first pages of the PDFs itself

The first 1 or 2 pages of a PDF are provided to the assitant in a thread.

Implemented in `extract_names_from_pdfs.py`. 

#### Idea 2. Assistant is provided with extracted text

The first 1 or 2 pages of a PDF are converted into images, then text is extracted from these images.

Implemented in `extract_names_from_text.py`. 

**Dependencies:**

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

## JSON output
https://python.useinstructor.com/blog/2024/06/15/zero-cost-abstractions/