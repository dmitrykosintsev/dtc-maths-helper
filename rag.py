# This class implement RAG using the index from indexer and various LLMs
import os
import time
import logging
import json

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv

# Load variables
load_dotenv()
logging.basicConfig(level=logging.INFO)

base_url = os.getenv('OLLAMA_URL')
ollama_url = f"{base_url}/v1/"
print(os.getenv('OLLAMA_URL'))
ollama_client = OpenAI(
    #base_url=os.getenv('OLLAMA_URL'),
    base_url=ollama_url,
    api_key="ollama",
)
OpenAI.api_key = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI()
model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")


def elastic_search(query, vector, index_name = "math_problems", top_k=10):
    search_query = {
        "size": 10,
        "query": {
            "bool": {
                "must": [
                    {
                        "match": {
                            "question": query  # Search the question field for the text query
                        }
                    }
                ],
                "should": [
                    {
                        "script_score": {
                            "query": {"match_all": {}},  # A match_all query to combine with vector search
                            "script": {
                                "source": """
                                        cosineSimilarity(params.query_vector, 'question_vector') + 1.0
                                    """,
                                "params": {
                                    "query_vector": vector  # Vector representation of the query
                                }
                            }
                        }
                    }
                ]
            }
        }
    }
    #print("Search Query:", search_query)
    es = Elasticsearch(os.getenv('ELASTIC_URL'))
    response = es.search(index=index_name, body=search_query)
    return response['hits']['hits']

# Define the prompt to send to LLM
def build_prompt(query, search_results):
    prompt_template = """
        You're a math teacher that provides support to students.
        Compare the question provided with the SOLUTION and ANSWER from the database.
        If the student's answer is wrong, explain the SOLUTION from the database.
        Explain how the SOLUTION is different from the answer provided by the student.
        Give your answer in a markdown format supported by Streamlit if using formulae.

        QUESTION: {question}

        STUDENT'S ANSWER: {answer}

        CONTEXT:
        {context}
        """.strip()

    # Format the context based on search results
    context = "\n\n".join(
        [
            f"section: {doc['section']}\nquestion: {doc['question']}\nanswer: {doc['answer']}"
            for doc in search_results
        ]
    )

    # Format the prompt with the query details
    return prompt_template.format(question=query['question'], answer=query['answer'], context=context).strip()


def llm(prompt, llmmodel="qwen2-math-7b-instruct"):
    start_time = time.time()
    try:
        logging.info(f"Sending request to Ollama. URL: {ollama_url}, Model: {llmmodel}")
        if llmmodel == 'qwen2-math-7b-instruct' or llmmodel == 'mathcoder-cl-7b' or llmmodel == 'deepseek-math-7b':
            response = ollama_client.chat.completions.create(
                model=llmmodel,
                messages=[{"role": "user", "content": prompt}]
            )
            logging.info("Received response from Ollama")
            answer = response.choices[0].message.content
        elif llmmodel == 'gpt-4o-mini':
                response = openai_client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[{"role": "user", "content": prompt}]
                )
                answer = response.choices[0].message.content
        else:
                raise ValueError(f"Unknown model choice: {llmmodel}")

        end_time = time.time()
        response_time = end_time - start_time
        print("Response time: {response_time}")
        return answer, response_time
    except Exception as e:
        logging.error(f"Error connecting to Ollama: {str(e)}")
        logging.error(f"Request details - URL: {ollama_url}, Model: {llmmodel}, Prompt: {prompt}")
        raise

# Prompt for LLM-as-a-judge evaluation
def evaluation_function(feedback, question, student_answer):
    eval_prompt_template = """
        You're a math evaluation system.
        Evaluate the RELEVANCE of the feedback provided by the teacher for the student's answer.
        Here is the data for evaluation:
            QUESTION: {question}
            STUDENT'S ANSWER: {student_answer}
            FEEDBACK: {feedback}

        Please analyze the content and context of the generated answer in relation to the original
        answer and provide your evaluation in parsable JSON without using code blocks:

        {{
          "Relevance": "NON_RELEVANT" | "PARTLY_RELEVANT" | "RELEVANT",
          "Explanation": "[Provide a brief explanation for your evaluation]"
        }}
        """.strip()

    prompt = eval_prompt_template.format(question=question, student_answer=student_answer, feedback=feedback)
    evaluation, _ = llm(prompt, 'gpt-4o-mini')

    try:
        json_eval = json.loads(evaluation)
        return json_eval['Relevance'], json_eval['Explanation']
    except json.JSONDecodeError:
        return "UNKNOWN", "Failed to parse evaluation"

def rag(query, llmmodel="qwen2-math-7b-instruct", eval_llm="gpt-4o-mini",):
    q = query['question']
    print("q is: ", q)
    vector = model.encode(q)
    search_results = elastic_search(q, vector)
    prompt = build_prompt(query, search_results)
    response, response_time = llm(prompt, llmmodel)
    query["response_time"] = response_time

    # Evaluate the relevance of the response from LLM
    relevance, explanation = evaluation_function(response, query['question'], query['answer'])

    query["analysis"] = response
    query["relevance"] = relevance
    query["rel_explanation"] = explanation
    query["model_used"] = llmmodel
    return query

def main():
    query = {
        "question": "A taxi ride costs $\$1.50$ plus $\$0.25$ per mile traveled.  How much, in dollars, does a 5-mile taxi ride cost?",
        "answer": "The answer is 2.75 because 0.25*5 + 1.5.",
        "analysis": "",
        "response_time": "",
        "relevance": "",
        "rel_explanation": "",
        "model_used": ""
    }

    print(rag(query))

if __name__ == "__main__":
    main()
