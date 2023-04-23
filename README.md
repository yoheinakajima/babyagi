# "BabyAGI with enhanced reasoning capabilities ...
![image](https://github.com/robiwan303/babyagi/blob/main/BabyAGI_Reasoning.jpeg)
# ... making it possible to achieve the ultimate objective"

<<<<<<<<<<<<<<<<<<<<<<<

This is a side branch of the BabyAGI main branch for an enhanced reasoning feature,... the LLM does determine on its own when the ultimate objective is (sufficiently) achieved.

I did also add a mechanism to have the LLM judge on the level of contribution for each task result, with respect to the ultimate objective. When the decision is made to come to an end, a final prompt is triggered. Handling of multi-part responses (for longer text) is implemented.

Since I felt approaches involving counters or other "coded" solutions are suboptimal, I tried another route: Definition of a stop criteria and modification of agent function prompts, so that the ultimate objective is followed more closely and the stop criteria is considered.
Last but not least I did implent a simple function for writing the terminal output to a text file.

I am still testing and fine-tuning the functionality. Due to the many commits to the main branch I am not able to catch up, so I will keep it in this side branch for the time being...

<<<<<<<<<<<<<<<<<<<<<<<

In the following screenshot you can see the solution to the objective "Solve world hunger" from .env.example... :-D

![image](https://github.com/robiwan303/babyagi/blob/main/Solve_world_hunger.jpeg)

I did use the plausi feature in order to reduce the time to completion, w/o might take a while for such a complex goal. Due to the heavy usage of OpenAI API, I am getting rate limit errors constantly. Therefore the final response is truncated, should have been at least two parts. The mechanism for triggering of multiple responses did work, but the rate limit did hit hard...

<<<<<<<<<<<<<<<<<<<<<<<

# Parameters for ultimate objective in .env:

OBJECTIVE=Same as for main branch, the ultimate objective

STOP_CRITERIA=The condition under which the ultimate objective is achieved

PLAUSI_NUMBER=Plausibilization is done based on the latest task result's contribution to the ultimate objective. Each completed task gets evaluated and a percentage value is assigned. After a factor is applied (value*0.01). The values are added up each cycle and checked if greater than the PLAUSI_NUMBER.

FINAL_PROMPT=Description for action which shall be executed when the ultimate objective (or enough plausibility) has been achieved, before stopping the script

<<<<<<<<<<<<<<<<<<<<<<<

The STOP_CRITERIA is pretty generic and should fit for most applications. The FINAL_PROMPT depends on what shall be achieved.

Hints for these prompts:
   - The wording in STOP_CRITERIA has a significant impact on when this condition will be met. For example see "When the ultimate objective has been achieved and is plausible" vs. "... has been achieved in an adequate manner and is plausible". This makes a big difference, since in the second case the LLM will determine on its own what is "adequate" in this case.
   - The next part in the predefined STOP_CRITERA ", or when further evaluation will most probably not improve the result" has been added as a safety condition to make sure that the process in finite and at some point the condition will be met.
   - The intention behind the FINAL_PROMPT is to have the final result reported in as many subsequent responses as necessary. Therefore I did implement the mechanism for triggering of the next part of the response. Unfortunately, due my API rate limit error problem, this does not work for me. But the mechanism is working otherwise the final line and pogram exit would not be reached.

See below the original README.md from BabyAGI main branch.

<<<<<<<<<<<<<<<<<<<<<<<

------------------------------------------------------------------------------------

# Translations:

[<img title="Français" alt="Français" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/fr.svg" width="22">](docs/README-fr.md)
[<img title="Polski" alt="Polski" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/pl.svg" width="22">](docs/README-pl.md)
[<img title="Portuguese" alt="Portuguese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/br.svg" width="22">](docs/README-pt-br.md)
[<img title="Romanian" alt="Romanian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ro.svg" width="22">](docs/README-ro.md)
[<img title="Russian" alt="Russian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ru.svg" width="22">](docs/README-ru.md)
[<img title="Slovenian" alt="Slovenian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/si.svg" width="22">](docs/README-si.md)
[<img title="Spanish" alt="Spanish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/es.svg" width="22">](docs/README-es.md)
[<img title="Turkish" alt="Turkish" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tr.svg" width="22">](docs/README-tr.md)
[<img title="Ukrainian" alt="Ukrainian" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ua.svg" width="22">](docs/README-ua.md)
[<img title="简体中文" alt="Simplified Chinese" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/cn.svg" width="22">](docs/README-cn.md)
[<img title="繁體中文 (Traditional Chinese)" alt="繁體中文 (Traditional Chinese)" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/tw.svg" width="22">](docs/README-zh-tw.md)
[<img title="日本語" alt="日本語" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/jp.svg" width="22">](docs/README-ja.md)
[<img title="한국어" alt="한국어" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/kr.svg" width="22">](docs/README-ko.md)
[<img title="Magyar" alt="Magyar" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/hu.svg" width="22">](docs/README-hu.md)
[<img title="فارسی" alt="فارسی" src="https://cdn.staticaly.com/gh/hjnilsson/country-flags/master/svg/ir.svg" width="22">](docs/README-fa.md)

# Objective

This Python script is an example of an AI-powered task management system. The system uses OpenAI and Chroma to create, prioritize, and execute tasks. The main idea behind this system is that it creates tasks based on the result of previous tasks and a predefined objective. The script then uses OpenAI's natural language processing (NLP) capabilities to create new tasks based on the objective, and Chroma to store and retrieve task results for context. This is a pared-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023).

This README will cover the following:

- [How the script works](#how-it-works)

- [How to use the script](#how-to-use)

- [Supported Models](#supported-models)

- [Warning about running the script continuously](#continous-script-warning)

# How It Works<a name="how-it-works"></a>

The script works by running an infinite loop that does the following steps:

1. Pulls the first task from the task list.
2. Sends the task to the execution agent, which uses OpenAI's API to complete the task based on the context.
3. Enriches the result and stores it in [Chroma](docs.trychroma.com).
4. Creates new tasks and reprioritizes the task list based on the objective and the result of the previous task.
   </br>

![image](https://user-images.githubusercontent.com/6764957/232961802-e4c4c17d-b520-4db1-827c-a218a1647c73.png)

The execution_agent() function is where the OpenAI API is used. It takes two parameters: the objective and the task. It then sends a prompt to OpenAI's API, which returns the result of the task. The prompt consists of a description of the AI system's task, the objective, and the task itself. The result is then returned as a string.
</br>
The task_creation_agent() function is where OpenAI's API is used to create new tasks based on the objective and the result of the previous task. The function takes four parameters: the objective, the result of the previous task, the task description, and the current task list. It then sends a prompt to OpenAI's API, which returns a list of new tasks as strings. The function then returns the new tasks as a list of dictionaries, where each dictionary contains the name of the task.
</br>
The prioritization_agent() function is where OpenAI's API is used to reprioritize the task list. The function takes one parameter, the ID of the current task. It sends a prompt to OpenAI's API, which returns the reprioritized task list as a numbered list.

Finally, the script uses Chroma to store and retrieve task results for context. The script creates a Chroma collection based on the table name specified in the TABLE_NAME variable. Chroma is then used to store the results of the task in the collection, along with the task name and any additional metadata.

# How to Use<a name="how-to-use"></a>

To use the script, you will need to follow these steps:

1. Clone the repository via `git clone https://github.com/yoheinakajima/babyagi.git` and `cd` into the cloned repository.
2. Install the required packages: `pip install -r requirements.txt`
3. Copy the .env.example file to .env: `cp .env.example .env`. This is where you will set the following variables.
4. Set your OpenAI API key in the OPENAI_API_KEY and OPENAPI_API_MODEL variables.
5. Set the name of the table where the task results will be stored in the TABLE_NAME variable.
6. (Optional) Set the name of the BabyAGI instance in the BABY_NAME variable.
7. (Optional) Set the objective of the task management system in the OBJECTIVE variable.
8. (Optional) Set the first task of the system in the INITIAL_TASK variable.
9. Run the script: `python babyagi.py`

All optional values above can also be specified on the command line.

# Running inside a docker container

As a prerequisite, you will need docker and docker-compose installed. Docker desktop is the simplest option https://www.docker.com/products/docker-desktop/

To run the system inside a docker container, setup your .env file as per steps above and then run the following:

```
docker-compose up
```

# Supported Models<a name="supported-models"></a>

This script works with all OpenAI models, as well as Llama and its variations through Llama.cpp. Default model is **gpt-3.5-turbo**. To use a different model, specify it through LLM_MODEL or use the command line.

## Llama

Llama integration requires llama-cpp package. You will also need the Llama model weights. 

- **Under no circumstances share IPFS, magnet links, or any other links to model downloads anywhere in this repository, including in issues, discussions or pull requests. They will be immediately deleted.**

Once you have them, set LLAMA_MODEL_PATH to the path of the specific model to use. For convenience, you can link `models` in BabyAGI repo to the folder where you have the Llama model weights. Then run the script with `LLM_MODEL=llama` or `-l` argument.

# Warning<a name="continous-script-warning"></a>

This script is designed to be run continuously as part of a task management system. Running this script continuously can result in high API usage, so please use it responsibly. Additionally, the script requires the OpenAI and Pinecone APIs to be set up correctly, so make sure you have set up the APIs before running the script.

# Contribution

Needless to say, BabyAGI is still in its infancy and thus we are still determining its direction and the steps to get there. Currently, a key design goal for BabyAGI is to be _simple_ such that it's easy to understand and build upon. To maintain this simplicity, we kindly request that you adhere to the following guidelines when submitting PRs:

- Focus on small, modular modifications rather than extensive refactoring.
- When introducing new features, provide a detailed description of the specific use case you are addressing.

A note from @yoheinakajima (Apr 5th, 2023):

> I know there are a growing number of PRs, appreciate your patience - as I am both new to GitHub/OpenSource, and did not plan my time availability accordingly this week. Re:direction, I've been torn on keeping it simple vs expanding - currently leaning towards keeping a core Baby AGI simple, and using this as a platform to support and promote different approaches to expanding this (eg. BabyAGIxLangchain as one direction). I believe there are various opinionated approaches that are worth exploring, and I see value in having a central place to compare and discuss. More updates coming shortly.

I am new to GitHub and open source, so please be patient as I learn to manage this project properly. I run a VC firm by day, so I will generally be checking PRs and issues at night after I get my kids down - which may not be every night. Open to the idea of bringing in support, will be updating this section soon (expectations, visions, etc). Talking to lots of people and learning - hang tight for updates!

# Inspired projects

In the short time since it was release, BabyAGI inspired many projects. You can see them all [here](docs/inspired-projects.md).

# Backstory

BabyAGI is a pared-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023) shared on Twitter. This version is down to 140 lines: 13 comments, 22 blanks, and 105 code. The name of the repo came up in the reaction to the original autonomous agent - the author does not mean to imply that this is AGI.

Made with love by [@yoheinakajima](https://twitter.com/yoheinakajima), who happens to be a VC (would love to see what you're building!)
