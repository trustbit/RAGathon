# Answer by Majority Vote

The intention of this app is that for our collective answer to each question, we each run our individual answer and choose the one that has a majority.

## Setup

Create a `.env` file containing an OpenAI API key. Example:

```
OPENAI_API_KEY=sk-proj-thisisafakeapikey
```

Install requirements.
```
pip install -r requirements.txt
```

## Adding your solution

Make a python package like `daniel`. It should have a function
like this:

```
def answer_question(question, schema):
   ...
```

Include this function in the list `answer_functions` in `__main__.py`.

## Running it

```
python -m majority_vote
```