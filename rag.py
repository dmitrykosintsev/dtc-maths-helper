# This class implement RAG using the index from indexer and various LLMs
import time
import os

from elasticsearch import Elasticsearch
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from dotenv import load_dotenv


# Load variables
load_dotenv()

ollama_client = OpenAI(
    base_url='http://localhost:11434/v1',
    api_key="ollama",
)
OpenAI.api_key = os.getenv('OPENAI_API_KEY')
openai_client = OpenAI()
model = SentenceTransformer("multi-qa-MiniLM-L6-cos-v1")


# def elastic_search(query, vector):
#     # Test text search alone
#     text_search_query = {
#         "query": {
#             "match": {"text": query}
#         }
#     }
#
#     # Test vector search alone
#     vector_search_query = {
#         "query": {
#             "script_score": {
#                 "query": {"match_all": {}},
#                 "script": {
#                     "source": "cosineSimilarity(params.vector, 'vector_field') + 1.0",
#                     "params": {"vector": vector}
#                 }
#             }
#         }
#     }
#
#     # Log the queries for debugging
#     print(f"Text search query: {text_search_query}")
#     print(f"Vector search query: {vector_search_query}")
#
#     # Run the combined query or either text/vector search individually
#     es = Elasticsearch('http://localhost:9200')
#     response = es.search(index="math_problems", body={"query": text_search_query})
#     return response["hits"]["hits"]


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
        Give your answer in a markdown format if using formulae.

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
    # Log the start time
    start_time = time.time()

    response = ollama_client.chat.completions.create(
        model=llmmodel,
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content

    end_time = time.time()
    response_time = end_time - start_time
    print("Response time: {response_time}")
    return answer

def rag(query, llmmodel="qwen2-math-7b-instruct"):
    q = query['question']
    print("q is: ", q)
    vector = model.encode(q)
    search_results = elastic_search(q, vector)
    prompt = build_prompt(query, search_results)
    response = llm(prompt, llmmodel)
    query["analysis"] = response
    return query

def main():
    query = {
        "question": "A taxi ride costs $\$1.50$ plus $\$0.25$ per mile traveled.  How much, in dollars, does a 5-mile taxi ride cost?",
        "answer": "The answer is 2.75 because 0.25*5 + 1.5.",
        "analysis": ""
    }

    print(rag(query))

# if __name__ == "__main__":
#     main()
