# Math helper

## Problem statement
This chatbot is created in order to provide students with a tool that will allow them to practice solving various maths problems with an immediate feedback about their solution. To my knowledge, there are no popular systems that work in this way.

Here are a few chatbots that work with maths:
* MathGPT by Mathful: can be used to solve questions. However, the user has to be familiar with prompt writing to get feedback for their solution.
* MathChat: this is a research project that should be deployed. Moreover, the framework is built upon ChatGPT-4o, and the author notes the LLM struggles to solve complex questions.
* DeepAI's Math AI: the closest solution to allow for conversations. However, it provides solutions to questions by default.

## Tech stack
**Search:** Elasticsearch 8.4.3

**Code**: Python 3.12

**UI**: Streamlit:latest

**LLMs:** deepseek-math-7b-rl, Qwen2-Math-7B-Instruct, MathCoder-CL-7B, chatGPT-4o-mini

**Database:** Postgres

**Container**: docker-compose

**Visualisation**: Grafana

## Installation

1. Clone the repository
~~~
git clone https://github.com/dmitrykosintsev/dtc-maths-helper
~~~
2. Edit .env.template to include your OpenAI API Key (if you want to run the bot using ChatGPT)
3. Follow the steps specific for your machine

### Linux
1. Give executable permissions to the install.sh script. This script runs all steps for you:
~~~
chmod +x /path/to/yourscript.sh
~~~
2. Run the script and relax:
~~~
./install.sh
~~~
3. After the script finishes with a success message, run 

4. If you do not wish to run unknown scripts from unknown sources (which means you are awesome!), you can simply go through the script step-by-step

### Windows
If you know how to run WSL, you should be able to install and run the app using the subsection for Linux.
If you are not familiar with WSL, use Codespaces and run the script as described in the Linux subsection.

### Mac
Not tested, but you should be able to run the commands used for Linux.