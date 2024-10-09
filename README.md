# Math helper

## Problem statement
This chatbot is created in order to provide students with a tool that will allow them to practice solving various maths problems with an immediate feedback about their solution. To my knowledge, there are no popular systems that work in this way.

Here are a few chatbots that work with maths:
* MathGPT by Mathful: can be used to solve questions. However, the user has to be familiar with prompt writing to get feedback for their solution.
* MathChat: this is a research project that should be deployed. Moreover, the framework is built upon ChatGPT-4o, and the author notes the LLM struggles to solve complex questions.
* DeepAI's Math AI: the closest solution to allow for conversations. However, it provides solutions to questions by default.

## Tech stack
**Search:** Elasticsearch 8.4.3 with Hybrid search

**Code**: Python 3.12

**UI**: Streamlit:latest

**Knowledgebase:** Math QSA dataset (https://www.kaggle.com/datasets/awsaf49/math-qsa-dataset)

**LLMs:** deepseek-math-7b-rl, Qwen2-Math-7B-Instruct, MathCoder-CL-7B, chatGPT-4o-mini

**Database:** Postgres

**Data ingestion:** Python script (see indexer.py)

**Container:** docker-compose

**Monitoring:** Grafana

## RAG flow


## Before you start
This manual assumes that you have Python installed either as part of your system or in a virtual environment. Setting virtual environment is not part of this manual. Kindly use Google or ChatGPT if you need help with this.

Based on my setup, installation might require **up to 25 GB on your HDD/SDD**.

The installation script is simple and is not guaranteed to run properly if the first run was interrupted. In this case, follow the steps for manual setup from the moment of interruption.

## Installing with a script

1. Clone the repository
~~~
git clone https://github.com/dmitrykosintsev/dtc-maths-helper
~~~
2. Edit .env.template to include your OpenAI API Key. By default, evaluation is done using GPT-4o-mini, though you can use any other model.
3. Follow the steps below

### Linux
4. Give executable permissions to the install.sh script. This script runs all the steps for you. Run the command from the directory where the script is located:
~~~
chmod +x install.sh
~~~
5. Run the script and relax:
~~~
./install.sh
~~~
6. After the script finishes with a success message, go to the section Running application

7. If you do not wish to run unknown scripts from unknown sources (which means you are awesome!), you can simply go through the script step-by-step

### Windows
If you know how to run WSL, you should be able to install and run the app using the subsection for Linux.
If you are not familiar with WSL, use Codespaces and run the script as described in the Linux subsection.

### Mac
Not tested, but you should be able to run the commands used for Linux.

## Installing manually
1. Clone the repository
~~~
git clone https://github.com/dmitrykosintsev/dtc-maths-helper
~~~
2. Edit .env.template to include your OpenAI API Key (if you want to run the bot using ChatGPT). Rename the file to .env
3. Create the following directories: ./data/postgres_data, ./data/grafana_data and ./.elasticsearch/data/
4. Run docker-compose build
5. Download models. You can get them all or pick one:
* deepseek-math-7b-rl:
    * https://huggingface.co/deepseek-ai/deepseek-math-7b-rl/blob/main/model-00001-of-000002.safetensors
    * https://huggingface.co/deepseek-ai/deepseek-math-7b-rl/blob/main/model-00002-of-000002.safetensors
* Qwen2-Math-7B-Instruct
    * https://huggingface.co/Qwen/Qwen2-Math-7B-Instruct/blob/main/model-00001-of-00004.safetensors
    * https://huggingface.co/Qwen/Qwen2-Math-7B-Instruct/blob/main/model-00002-of-00004.safetensors
    * https://huggingface.co/Qwen/Qwen2-Math-7B-Instruct/blob/main/model-00003-of-00004.safetensors
    * https://huggingface.co/Qwen/Qwen2-Math-7B-Instruct/blob/main/model-00004-of-00004.safetensors
* MathCoder-CL-7B
    * https://huggingface.co/MathLLMs/MathCoder-CL-7B/blob/main/model-00001-of-00002.safetensors
    * https://huggingface.co/MathLLMs/MathCoder-CL-7B/blob/main/model-00002-of-00002.safetensors

Download each model into a separate directory and create Modelfile in each directory.
The content of Modelfile:
~~~
FROM /path/to/safetensors/directory
~~~
6. To import a model into Ollama, its files and Modelfile should be copied in OLLAMA_MODELS folder (set in .env file, default ./ollama/models/).
~~~
docker-compose up -d ollama
~~~
and
~~~
docker exec -it ollama bash
~~~
Then, run:
~~~
ollama create <modelname>
~~~
Without leaving the bash terminal, you can check that the model is imported by using the following command:
~~~
ollama list
~~~~
Return to your standard terminal and run:
~~~
docker-compose up -d elasticsearch
~~~
to run elasticsearch. After, execute the indexer script to index the csv file with problems and solutions:
~~~
python3 indexer.py
~~~
Run newdb.py to initialise the database:
~~~
python3 newdb.py
~~~

## Running application
1. Run docker-compose from the root folder of the project:
~~~
docker-compose up -d
~~~
2. Look for the output from Streamlit to find the access link for the application.

### Interface
Chatbot:
[streamlit-app-2024-10-08-00-10-98.webm](https://github.com/user-attachments/assets/76a39a76-05f6-417c-bf17-01f4829236f8)

Monitoring dashboard:
![Grafana](https://github.com/user-attachments/assets/e7dae241-6603-40e4-8dea-5f93e83c914b)


### Using NVidia GPUs:
Uncomment the following lines in docker-compose.yaml if you have a dedicated NVidia GPU and want to use it for Ollama:
~~~
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [ gpu ]
~~~

## Evaluations

### Retrieval evaluation
Not conducted. Hybrid search is used out of the box:
~~~python
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
~~~

### RAG evaluation
The following part of rag.py is responsible for LLM-as-a-judge evaluation:
~~~python
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
~~~
