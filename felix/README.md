# README

First try of Felix Krause for TAT internal RAG challenge.

## Architecture (overview)
Multiagent ChatGPT based solution, with 3 characters:
- Delegation Manager (delegating smaller tasks to company experts) 
- Company Expert (answering specific questions about the company)
- Execution Manager (deciding on final answer based on answers of company experts and their chain of thought.)


## Architecture (text-based)
This solution is based on three specialized agents using ChatGPT 4o, each with a specific role in the 
decision making process. A delegation manager is responsible for delegating simple tasks to company experts. It 
enhances the user queries to allow for a better understanding of the context and the question. The company 
experts are specialized in answering questions about a specific company report. They are responsible for extracting 
the relevant information from the context, which contains the results of a basic vector database with chunk 
size 3000. Based on this they will provide an answer according to the guidelines and also a concise explanation of 
their decision process. The execution manager is then responsible for deciding on the final answer based on the 
answers and chains of thought of the company experts. While the company experts might be very strict in providing 
answers based on the query, the execution manager tries to capture the whole picture and might deviate from the 
answers of the company experts. 


## Results
`results_v1.json` (to v7) contains solutions to sample questions [online](https://github.com/trustbit/enterprise-rag-challenge/blob/main/samples/questions.json).
`results_v8.json` contains solutions to actual questions for evaluation.

The respective log files contain the chain of thought of the agents for each question, allowing for a detailed 
analysis of the decision making process. 


## Next Steps/TODOs
- extract most important tables in pdfs as dataframes and get them immediately into context?
- Question generator for competition will hide some of the questions (not fully sure?)
- Provide calculator to architecture?
- Include definition/explanation of financial metrics from question generator