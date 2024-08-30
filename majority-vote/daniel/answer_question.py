import os
import json
from datetime import datetime
from pydantic import BaseModel
from typing import Optional

OPENAI_MODEL = "gpt-4o-2024-08-06"
KNOWLEDGE_BASE_PATH = 'daniel/knowledge_base'


# Initialize an empty list to store the dictionaries
json_list = []

# Iterate over each file in the directory
for filename in os.listdir(KNOWLEDGE_BASE_PATH):
    if filename.endswith('.json'):  # Check if the file is a JSON file
        filepath = os.path.join(KNOWLEDGE_BASE_PATH, filename)
        with open(filepath, 'r') as json_file:
            data = json.load(json_file)  # Load the JSON file into a dict
            json_list.append(data)  # Append the dict to the list

# Now json_list contains all the JSON files as dicts
database = [
    {
        "company_name": x["company_name"],
        "data_points": x["data_points"],
        "role_assignments": x["role_assignments"]
    }
    for x in json_list
]

class NumberResponse(BaseModel):
    answer: Optional[float]


class NameResponse(BaseModel):
    person_name: Optional[str]


class BooleanResponse(BaseModel):
    answer: Optional[bool]


def answer_question(question, schema):
    system_prompt = ("You are an assistant with the task of answering QUESTIONS based on a KNOWLEDGE DATABASE. "
                     "If you cannot answer the question, indicate this with a `null` response. "
                     f"The current date is {datetime.today().strftime('%Y-%m-%d')}")

    prompt = ("QUESTION\n\n"
              f"{question}\n\n"
              "KNOWLEDGE DATABASE\n\n"
              f"{json.dumps(database)}")

    from openai import OpenAI
    client = OpenAI()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    match schema:
        case "number":
            response_format = NumberResponse
            value_extractor = lambda x: x.answer
        case "name":
            response_format = NameResponse
            value_extractor = lambda x: x.person_name
        case "boolean":
            response_format = BooleanResponse
            value_extractor = lambda x: x.answer
        case _:
            raise f"unknown schema {schema}"

    response = client.beta.chat.completions.parse(
        model=OPENAI_MODEL,
        messages=messages,
        response_format=response_format
    )

    return value_extractor(response.choices[0].message.parsed)
