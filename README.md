<h1 align="center">
 babyagi-langchain

</h1>

# Introduction
This Python script is implementation of [BabyAGI](https://github.com/yoheinakajima/babyagi) and LangChain's [BabyAGI with Tools](https://python.langchain.com/en/latest/use_cases/agents/baby_agi_with_agent.html).  This leverages FAISS for vector database and SerperAPI for easy searching engine scraping.  This code base is inspired by BabyAGI and LangChain see Acknowledgements section below.

# Warning<a name="continous-script-warning"></a>
This script is designed to be run continuously as part of a task management system. Running this script continuously can result in high API usage, so please use it responsibly. Additionally, the script requires the OpenAI and SerpAPI APIs to be set up correctly, so make sure you have set up the APIs before running the script.

# How to Use

## Pre-requisite
You need OpenAI and SerpAPI API key for the LLM and Search feature.


To use the script, you will need to follow these steps:

1. Clone the repository via `git clone https://github.com/realminchoi/babyagi-langchain.git` and `cd` into the cloned repository.
2. Install the required packages: `pip install -r requirements.txt`
3. Copy the .env.example file to .env: `cp .env.example .env`. This is where you will set the following variables.
4. Set your OpenAI and SerperAPI API keys in the OPENAI_API_KEY, and SERPAPI_API_KEY variables.
5. Set additional variables such as MAX_ITERATIONS, OBJECTIVE, FIRST_TASK

## Usage

Run BabyAGI.
````
python babyagi.py 
````

# Acknowledgments

I would like to express my gratitude to the developers whose code I referenced in creating this repo.

Special thanks go to 

@yoheinakajima (https://github.com/yoheinakajima/babyagi)

@hinthornw (https://github.com/hwchase17/langchain/pull/2559)