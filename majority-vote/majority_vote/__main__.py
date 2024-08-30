import json
import random
from collections import Counter
from typing import Callable, Optional

import daniel.answer_question

from dotenv import load_dotenv


def majorities(items):
    # Count occurrences of each item
    counts = Counter(items)

    # Find the maximum occurrence
    max_count = max(counts.values())

    # Extract items that have the maximum occurrence
    result = [item for item, count in counts.items() if count == max_count]

    return result


def majority_vote(items):
    result = majorities(items)
    # If there's a tie, return a random item from those that are tied.
    return random.choice(result)

load_dotenv()

AnswerFunction = Callable[[str, str], Optional[str]]

answer_functions = [ daniel.answer_question.answer_question ]

results = []

with open('questions.json', 'r') as json_file:
    items = json.load(json_file)

    for item in items:
        question = item["question"]
        print(f"Processing question: {question}")

        answers = [ answer_question(question, item["schema"]) for answer_question in answer_functions]
        answer = majority_vote(answers)

        print(f"Answer: {answer}")

        results.append({
            "question": question,
            "schema": item["schema"],
            "answer": answer
        })

with open('results.json', 'w') as json_file:
    json.dump(results, json_file, indent=4)