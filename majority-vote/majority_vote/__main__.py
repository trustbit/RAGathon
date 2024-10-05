import json
import random
from collections import Counter
from typing import Callable, Optional

import sample

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
    not_none_items = [item for item in items if item is not None]
    # Only return None if all items are None.
    if len(not_none_items) == 0:
        return None
    else:
        result = majorities(items)
        # If there's a tie, return a random item from those that are tied.
        return random.choice(result)

load_dotenv()

AnswerFunction = Callable[[str, str], Optional[str]]

# TODO: Remove the sample answer_question function; add real functions.
answer_functions = [ sample.answer_question ]

results = []

with open('questions.json', 'r') as json_file:
    items = json.load(json_file)

    for item in items:
        question = item["question"]
        print(f"Processing question: {question}")

        answers = [ answer_question(question, item["schema"]) for answer_question in answer_functions ]
        print(f"All answers: {answers}")

        answer = majority_vote(answers)
        print(f"Chosen answer: {answer}")
        print()

        results.append({
            "question": question,
            "schema": item["schema"],
            "answer": "n/a" if answer is None else answer
        })

with open('results.json', 'w') as json_file:
    json.dump(results, json_file, indent=4)