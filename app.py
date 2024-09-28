import streamlit as st
from elasticsearch import Elasticsearch
import random
from rag import rag

# Initialize Elasticsearch client
es = Elasticsearch("http://localhost:9200")  # Adjust this URL to your Elasticsearch setup

# Function to retrieve a random question from Elasticsearch
def get_random_question():
    # Generate a seed for randomization
    seed = random.randint(0, 7498)

    # Elasticsearch query to fetch a random question
    search_query = {
        "size": 7498,  # Fetch one random question
        "query": {
            "function_score": {
                "query": {"match_all": {}},  # Match all documents
                "random_score": {
                    "seed": seed,  # Use the seed for random scoring
                    "field": "question_id"  # Use the numeric field
                }
            }
        }
    }

    # Perform search in the "math_problems" index
    response = es.search(index="math_problems", body=search_query)

    # Extract the questions from the response
    hits = response["hits"]["hits"]
    questions = [hit["_source"]["problem"] for hit in hits]

    # Select a random question
    if questions:
        return random.choice(questions)
    else:
        return "No questions found in the index."

# Streamlit app for the math support bot
def main():
    st.title("Math Support Bot")
    st.text("This bot provides a random math problem \nand analyses student's solution for mistakes.")

    # Restart button to fetch a new question
    if st.button("Get another question"):
        del st.session_state.question
        del st.session_state.answer

    if "question" not in st.session_state:
        st.session_state.question = get_random_question()

    st.markdown(f"Question: {st.session_state.question}")

    # Input field for student's answer
    answer = st.text_area("Your answer:", key="answer")

    # Send button to submit the answer
    if st.button("Send"):
        # Dummy context and response for now
        query = {
            "question": st.session_state.question,
            "answer": answer,
            "analysis": ""
        }
        llm_response = rag(query)

        # Display the response from LLM
        st.write("Response from the bot:")
        st.markdown(llm_response['analysis'])

if __name__ == "__main__":
    main()
