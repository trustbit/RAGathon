import instructor
from openai import OpenAI
import os
import re
import json
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import Optional
import PyPDF2
from extract_names_from_text import find_all_names


SAMPLE_DATA_PATH = "data/samples"
RULES = """
1. For a "Number" type question, provide only a metric number or None as the answer, and **nothing else**. The number should not include decimal commas, spaces, or separators.
2. For a "Name" type question, provide only the exact name of the company or None as it appears in the dataset, and **nothing else**. The name must match exactly.
3. For a "Boolean" type question, provide only True, False or None, and **nothing else**. The case of the letters does not matter.
4. Important: For any question (number, name or boolean) if the answer is unknown or cannot be determined, use None.
"""


class NumberResponse(BaseModel):
    answer: Optional[float]

class NameResponse(BaseModel):
    answer: Optional[str]

class BooleanResponse(BaseModel):
    answer: Optional[bool]


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

openai_client = OpenAI(api_key=api_key)
instructor_client = instructor.from_openai(OpenAI(api_key=api_key))

pdf_names, names_cost = find_all_names(openai_client, SAMPLE_DATA_PATH)

with open(os.path.join(SAMPLE_DATA_PATH, "questions.json")) as f:
    json_data = json.load(f)
    for item in json_data:
        if item['schema'] == "number":
            response_class = NumberResponse
        elif item['schema'] == "name":
            response_class = NameResponse
        elif item['schema'] == "boolean":
            response_class = BooleanResponse
        else:
            continue 
        
        # This approach doesn't seem to work, completions can't takes files
        # file = openai_client.files.create(
        #     file=open(os.path.join(SAMPLE_DATA_PATH, "3696c1b29566acc1eafc704ee5737fb3ae6f3d1d.pdf"), "rb"),
        #     purpose="fine-tune"
        # )
        
        relevant_files = find_matching_files(item['question'], pdf_names)
        print(relevant_files)
        
        # This also doesn't work, because it's each to exceed the limit of 120000 input tokens
        text = ""
        for pdf_file in relevant_files:
            reader = PyPDF2.PdfReader(os.path.join(SAMPLE_DATA_PATH, pdf_file))
            for page in range(len(reader.pages)):
                text += reader.pages[page].extract_text()
        
        response, completion = instructor_client.chat.completions.create_with_completion(
            model="gpt-4o",
            response_model=response_class,
            messages=[
                {
                    "role": "system", 
                    "content": "You are a helpful assistant that can read PDFs."
                },
                {
                    "role": "user", 
                    "content": f"Based on the information this text: '{text}', "
                               f"answer this question: {item['question']}. "
                            #    f"Type of the response must be: {item['schema']}. "
                               f"Follow these rules: {RULES}"
                }
            ],
        )
        
        if response.answer is not None:
            item['answer'] = response.answer
        else:
            item['answer'] = "n/a"
            
        print("RESPONSE: ", response)
        # TODO: sum up tokens and cost
        print(completion.usage)

    # print(json_data)
    
with open(os.path.join(SAMPLE_DATA_PATH, "questions_answers.json"), "w") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)