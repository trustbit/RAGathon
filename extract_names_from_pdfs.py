from openai import OpenAI
import pandas as pd
import os
import re
import random
import PyPDF2
from dotenv import load_dotenv
from maria.cost import get_run_cost


SAMPLE_DATA_PATH = "data/samples"
TITLE_PAGES_PATH = "data/processed/title_pages"
N_PAGES_TO_PROCESS = 2


def extract_first_n_pages(input_pdf, n_pages, output_pdf):
    with open(input_pdf, 'rb') as infile:
        reader = PyPDF2.PdfReader(infile)
        writer = PyPDF2.PdfWriter()
        for i in range(n_pages):
            writer.add_page(reader.pages[i])
        with open(output_pdf, 'wb') as outfile:
            writer.write(outfile)            
    
def get_thread_response(client, assistant_id, thread_id):
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id, assistant_id=assistant_id
    )
    messages = list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id))
    response = messages[0].content[0].text.value
    total_tokens, total_cost = get_run_cost(run)
    return response, total_tokens, total_cost

def get_company_name(pdf_file_path, client, assistant_id):
    pdf_file_name = os.path.basename(pdf_file_path)
    title_page_path = os.path.join(TITLE_PAGES_PATH, pdf_file_name)
    extract_first_n_pages(pdf_file_path, N_PAGES_TO_PROCESS, title_page_path)
    
    file = client.files.create(
        file=open(title_page_path, "rb"),
        purpose="assistants"
    )
    
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "Look at the first two pages of a company's financial report. "
                           "What is the name of the company? "
                           ### Apparently this file search doesn't have ocr capabilities
                           # "If there is no title, consider extracting the name from the logo. " 
                           "Return company's name and nothing else in the response. "
                           "If you don't know the name, respond 'Unknown'.",
                "attachments": [
                    {
                        "file_id": file.id,
                        "tools": [{"type": "file_search"}]
                    }
                ]
            }
        ]
    )
    
    return get_thread_response(client, assistant_id, thread.id)


def find_all_names(client, sample_data_path):
    assistant = client.beta.assistants.create(
        name="PDF reader",
        instructions="Find requested information in the provided pdf file.",
        tools=[{"type": "file_search"}],
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
            


load_dotenv()
api_key=os.environ.get("OPENAI_API_KEY_RAG_CHALLENGE")

client = OpenAI(api_key=api_key)

pdf_names, cost = find_all_names(client, SAMPLE_DATA_PATH)
print(f"pdf names: {pdf_names}")
print(f"Total tokens: {cost['total_tokens']}, total cost: ${cost['total_cost']:.6f}")
