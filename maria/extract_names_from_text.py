from openai import OpenAI
import os
import pytesseract
from pdf2image import convert_from_path
# import PyPDF2
from dotenv import load_dotenv
from cost import get_run_cost


SAMPLE_DATA_PATH = "data/samples"
N_PAGES_TO_PROCESS = 2


def extract_text_from_first_n_pages(input_pdf, n_pages):
    # Convert PDF pages to images
    pages = convert_from_path(input_pdf, first_page=1, last_page=n_pages)

    # Extract text using OCR
    text = ""
    for page in pages:
        text += pytesseract.image_to_string(page)

    # Alternatively, extract text directly (if PDF has selectable text)
    # reader = PyPDF2.PdfReader(input_pdf)
    # text = ""
    # for page in range(n_pages):
    #     text += reader.pages[page].extract_text()
    
    return text

    
def get_thread_response(client, assistant_id, thread_id):
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id, assistant_id=assistant_id
    )
    messages = list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id))
    response = messages[0].content[0].text.value
    total_tokens, total_cost = get_run_cost(run)
    return response, total_tokens, total_cost


def get_company_name(pdf_file_path, client, assistant_id):
    pdf_text = extract_text_from_first_n_pages(pdf_file_path, N_PAGES_TO_PROCESS)
    
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": f"Identify the company name from the following text: {pdf_text}. "
                            "Return only the company's name and nothing else in your response. "
                            "If the company name cannot be identified, respond with 'Unknown' and nothing else.",
            }
        ]
    )
    
    return get_thread_response(client, assistant_id, thread.id)


def find_all_names(client, sample_data_path):
    assistant = client.beta.assistants.create(
        name="Company name extractor",
        instructions="Extract the company name from the provided text. "
                     "Focus on identifying the official company name based on the content "
                     "available in the text.",
        model="gpt-4o",
    )
    
    pdf_names = {}
    cost = {
        'total_tokens': 0,
        'total_cost': 0
    }
    
    # Iterate through files
    for file_name in os.listdir(sample_data_path):
        if file_name.endswith(".pdf"):
            file_path = os.path.join(sample_data_path, file_name)
            company_name, total_tokens, total_cost = get_company_name(file_path, client, assistant.id)
            pdf_names[file_name] = company_name
            cost['total_tokens'] += total_tokens
            cost['total_cost'] += total_cost
    
    return pdf_names, cost
            

            
# load_dotenv()
# api_key=os.environ.get("OPENAI_API_KEY_RAG_CHALLENGE")

# client = OpenAI(api_key=api_key)

#pdf_names, cost = find_all_names(client, SAMPLE_DATA_PATH)
#print(f"pdf names: {pdf_names}")
#print(f"Total tokens: {cost['total_tokens']}, total cost: ${cost['total_cost']:.6f}")



