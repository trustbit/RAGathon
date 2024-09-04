from openai import OpenAI
import os
import re
import json
from dotenv import load_dotenv
from extract_names_from_text import find_all_names
from cost import get_run_cost


SAMPLE_DATA_PATH = "data/samples"
RULES = """
1. For a "Number" type question, provide only a metric number or None as the answer, and **nothing else**. The number should not include decimal commas, spaces, or separators.
2. For a "Name" type question, provide only the exact name of the company or None as it appears in the dataset, and **nothing else**. The name must match exactly.
3. For a "Boolean" type question, provide only True, False or None, and **nothing else**. The case of the letters does not matter.
4. Important: For any question (number, name or boolean) if the answer is unknown or cannot be determined, use None.
5. Don't provide links!
"""


def extract_names_from_string(input_string):
    # Find all substrings within double quotes
    quoted_substrings = re.findall(r'"(.*?)"', input_string)
    
    names = []
    for substring in quoted_substrings:
        # Split the substring into words
        words = substring.split()
        # Take the first one or two words and convert to lowercase
        first_words = ' '.join(words[:2]).lower()
        names.append(first_words)
    
    return names


def find_matching_files(input_string, dictionary):
    # Extract keywords from the input string
    names = extract_names_from_string(input_string)
    
    matching_files = []
    # Iterate through each keyword and check if it exists in any dictionary value
    for name in names:
        for key, value in dictionary.items():
            if name in value.lower():
                matching_files.append(key)
                break  # Stop searching once a match is found for this keyword
    
    return matching_files


load_dotenv()
api_key=os.environ.get("OPENAI_API_KEY_RAG_CHALLENGE")

client = OpenAI(api_key=api_key)

assistant = client.beta.assistants.create(
  name="Financial PDF Analyst",
  instructions="You are a financial data analyst specializing in extracting and analyzing information from PDF files. "
               "Your task is to search through the provided PDF files, which contain annual reports of various companies, "
               "and accurately answer questions based on the information found in those reports.",
  tools=[{"type": "file_search"}],
  model="gpt-4o",
)
assistant_id = assistant.id

pdf_names, names_cost = find_all_names(client, SAMPLE_DATA_PATH)
print(f"Company names: {pdf_names}")
print(f"Cost of extracting company names: {names_cost}")

with open(os.path.join(SAMPLE_DATA_PATH, "questions.json")) as f:
    json_data = json.load(f)
    total_usage = {
        'total_tokens': 0,
        'total_cost': 0
    }
    
    for item in json_data:
        print(f"Question: {item['question']}")
        
        relevant_files = find_matching_files(item['question'], pdf_names)
        print(relevant_files)
        
        if not relevant_files:
            print(f"No relevant files found for question: {item['question']}. Skipping to the next item.")
            item['answer'] = "n/a"
            continue
        
        file_ids = []
        for file_name in relevant_files:
            if file_name.endswith(".pdf"):
                file_path = os.path.join(SAMPLE_DATA_PATH, file_name)
                with open(file_path, "rb") as file:
                    response = client.files.create(
                        file=file,
                        purpose="assistants",
                    )
                    file_ids.append(response.id)
        
        thread = client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"Here is a document (or two documents). "
                               f"Based on the information in this document, "
                               f"answer this question: {item['question']} "
                               f"Type of the response must be: {item['schema']} or 'n/a'. "
                               f"Follow these rules: {RULES}",
                    "attachments": [
                        {
                            "file_id": file_id,
                            "tools": [{"type": "file_search"}]
                        } for file_id in file_ids
                    ]
                }
            ]
        )
        thread_id=thread.id
        
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread_id, assistant_id=assistant_id
        )
        messages = list(client.beta.threads.messages.list(thread_id=thread_id, run_id=run.id))
        print(messages)
        if messages and messages[0].content:
            response = messages[0].content[0].text.value
        else:
            print("No openai response")
            response = None
        tokens, cost = get_run_cost(run)
        
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