from openai import OpenAI
import pandas as pd
import os
import json
import PyPDF2
from dotenv import load_dotenv
from cost import get_run_cost


SAMPLE_DATA_PATH = "data/samples"
COMBINED_FILE = 'data/processed/combined/combined.pdf'

RULES = """
1. For a "Number" type question, provide only a metric number or None as the answer, and **nothing else**. The number should not include decimal commas, spaces, or separators.
2. For a "Name" type question, provide only the exact name of the company or None as it appears in the dataset, and **nothing else**. The name must match exactly.
3. For a "Boolean" type question, provide only True, False or None, and **nothing else**. The case of the letters does not matter.
4. Important: For any question (number, name or boolean) if the answer is unknown or cannot be determined, use None.
5. Don't provide links!
"""
            
# This is apparently not necessary, because you can also pass several files to a thread  
def combine_pdfs(folder_path, output_file):
    merger = PyPDF2.PdfMerger()

    for filename in sorted(os.listdir(folder_path)):
        if filename.endswith('.pdf'):
            filepath = os.path.join(folder_path, filename)
            merger.append(filepath)

    merger.write(output_file)
    merger.close()

    return output_file


load_dotenv()
api_key=os.environ.get("OPENAI_API_KEY_RAG_CHALLENGE")

client = OpenAI(api_key=api_key)

assistant = client.beta.assistants.create(
  name="Financial PDF Analyst",
  instructions="You are a financial data analyst specializing in extracting and analyzing information from PDF files. "
               "Your task is to search through the provided PDF file, which contain annual reports of various companies, "
               "and accurately answer questions based on the information found in those reports.",
  tools=[{"type": "file_search"}],
  model="gpt-4o",
)

combined_file = combine_pdfs(SAMPLE_DATA_PATH, COMBINED_FILE) 
        
file = client.files.create(
    file=open(combined_file, "rb"),
    # file=open("data/processed/combined/combined.pdf", "rb"),
    purpose="assistants"
)

thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": f"Here is the document we will be referring to. "
                       f"Based on the information in this document, "
                       f"answer my questions. "
                       f"Follow these rules: {RULES}",
            # TODO: Try multiple attachements
            "attachments": [
                {
                    "file_id": file.id,
                    "tools": [{"type": "file_search"}]
                }
            ]
        }
    ]
)

thread_id = thread.id
assistant_id = assistant.id

def ask_question(thread_id, assistant_id, question):
    # Create a new message in the existing thread with the question
    message = client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )

    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread_id, assistant_id=assistant_id
    )
    messages = list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id))
    response = messages[-1].content[0].text.value
    tokens, cost = get_run_cost(run)
    return response, tokens, cost

with open(os.path.join(SAMPLE_DATA_PATH, "questions.json")) as f:
    json_data = json.load(f)
    total_usage = {
        'total_tokens': 0,
        'total_cost': 0
    }
    for item in json_data:
        print(f"Question: {item['question']}")
        question = f"{item['question']} Type of the response must be: {item['schema']} or 'n/a'. "
        response, tokens, cost = ask_question(thread_id, assistant_id, question)
        
        if response in [None, "None"]:
            item['answer'] = "n/a"
        else:
            item['answer'] = response
        print("Response: ", response)
        
        total_usage['total_tokens'] += tokens
        total_usage['total_cost'] += cost
        print(f"Tokens: {tokens}, cost: {cost}")
        
with open(os.path.join(SAMPLE_DATA_PATH, "results.json"), "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)
print(total_usage)