from openai import OpenAI
import pandas as pd
import os
import re
import shutil
import json
from dotenv import load_dotenv
from cost import get_run_cost
from extract_names_from_text import find_all_names


SAMPLE_DATA_PATH = "data/samples"
RENAMED_DATA_PATH = "data/processed/renamed"

RULES = """
1. For a "Number" type question, provide only a metric number or None as the answer, and **nothing else**. The number should not include decimal commas, spaces, or separators.
2. For a "Name" type question, provide only the exact name of the company or None as it appears in the dataset, and **nothing else**. The name must match exactly.
3. For a "Boolean" type question, provide only True, False or None, and **nothing else**. The case of the letters does not matter.
4. Important: For any question (number, name or boolean) if the answer is unknown or cannot be determined, use None.
5. Don't provide links!
"""


def convert_to_valid_filename(input_string):
    valid_filename = re.sub(r'[<>:"/\\|?*]', '', input_string)
    valid_filename = valid_filename.replace(' ', '_')
    max_length = 255
    valid_filename = valid_filename[:max_length]
    return valid_filename


def rename_and_save_files(source_dir, dest_dir, name_mapping):
    os.makedirs(dest_dir, exist_ok=True)

    for old_name, new_name in name_mapping.items():
        old_file_path = os.path.join(source_dir, old_name)
        new_file_path = os.path.join(dest_dir, convert_to_valid_filename(new_name)+".pdf")

        if os.path.exists(old_file_path):
            shutil.copy(old_file_path, new_file_path)


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

pdf_names, names_cost = find_all_names(client, SAMPLE_DATA_PATH)
print(f"Cost of extracting company names: {names_cost}")
rename_and_save_files(SAMPLE_DATA_PATH, RENAMED_DATA_PATH, pdf_names)

renamed_files = os.listdir(RENAMED_DATA_PATH) 
file_ids = []
for file_name in renamed_files:
    if file_name.endswith(".pdf"):
        file_path = os.path.join(RENAMED_DATA_PATH, file_name)
        with open(file_path, "rb") as file:
            response = client.files.create(
                file=file,
                purpose="assistants",
                # Apparently gpt-4o will NOT see this additional meta info
                # extra_body={
                #     "company_name": pdf_names[file_name]
                # }
            )
            file_ids.append(response.id)


thread = client.beta.threads.create(
    messages=[
        {
            "role": "user",
            "content": f"Here are the documents we will be referring to. "
                       f"I will ask questions. You should identify relevant files "
                       f"by looking at the company names in the question and the file names, "
                       f"and then look for the answer only in those files. "
                       f"Answer my questions based on the info in the relevant files. "
                       f"Follow these rules: {RULES}",
            # Apparently the upper limit is 10 attachements
            "attachments": [
                {
                    "file_id": file_id,
                    "tools": [{"type": "file_search"}]
                } for file_id in file_ids
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

tokens_all_together = total_usage['total_tokens'] + names_cost['total_tokens']
cost_all_together = total_usage['total_cost'] + names_cost['total_cost']
print(f"All together, tokens: {tokens_all_together}, cost: ${cost_all_together}")