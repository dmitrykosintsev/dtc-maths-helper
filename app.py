import streamlit as st
from elasticsearch import Elasticsearch
import random
import os
import logging
from rag import rag

# Debugging logs
logging.basicConfig(level=logging.INFO)
logging.info(f"OLLAMA_URL: {os.getenv('OLLAMA_URL')}")
logging.info(f"Current working directory: {os.getcwd()}")
logging.info(f"Contents of current directory: {os.listdir()}")

# Initialize Elasticsearch client
es = Elasticsearch(os.getenv('ELASTIC_URL'))  # Adjust this URL to your Elasticsearch setup

# Function to print logs
def print_log(message):
    print(message, flush=True)

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
    print_log("Starting the Math chatbot")
    st.title("Math Support Bot")
    st.text("This bot provides a random math problem \nand analyses student's solution for mistakes.")

    if "question" not in st.session_state:
        st.session_state.question = get_random_question()

    if "answer" not in st.session_state:
        st.session_state.answer = ""  # Initialize answer as an empty string

    if "feedback" not in st.session_state:
         st.session_state.feedback = None  # Initialize feedback as None

    # Restart button to fetch a new question
    if st.button("Get another question"):
        st.session_state.question = get_random_question()
        st.session_state.answer = ""
        st.session_state.feedback = None

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

        # Ask for feedback from the user
        st.write("Did this help you?")
        col1, col2 = st.columns(2)

        feedback = None
        if col1.button("👍"):
            st.session_state.feedback = "positive"
        if col2.button("👎"):
            st.session_state.feedback = "negative"

    # Display feedback if it has been given
    if st.session_state.feedback:
        st.write(f"Thank you for your feedback: {st.session_state.feedback}")

if __name__ == "__main__":
    main()
