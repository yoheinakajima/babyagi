import os
import time
import openai
import pinecone
from dash import dcc, html
from collections import deque
from typing import Dict, List
import dash_bootstrap_components as dbc

OPEN_BUTTON = 'light'
OUTLINE_BUTTON = True
STYLE_BUTTON = {'border': 0}
CLOSE_BUTTON = 'primary'
FONT_SIZE = '1rem'

with open('config.env') as f:
    os.environ.update(
        line.replace('export ', '', 1).strip().split('=', 1) for line in f
        if 'export' in line
    )

# Set API Keys and Table configuration
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
OPENAI_API_MODEL = os.environ.get("OPENAI_API_MODEL")
PINECONE_API_KEY = os.environ.get('PINECONE_API_KEY')
PINECONE_ENVIRONMENT = os.environ.get("PINECONE_ENVIRONMENT")
YOUR_TABLE_NAME = os.environ.get("TABLE_NAME")
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = YOUR_TABLE_NAME
dimension = 1536
metric = "cosine"
pod_type = "p1"
if table_name not in pinecone.list_indexes():
    pinecone.create_index(
        table_name, dimension=dimension, metric=metric, pod_type=pod_type
    )

# Connect to the index
index = pinecone.Index(table_name)


def get_ada_embedding(text):
    """
    Gets the embedding for the specified text using the Ada model from OpenAI.

    Args:
        text (str): The text to get the embedding for.

    Returns:
        List[float]: A list of floating-point numbers representing the 
        embedding for the specified text.
    """
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]


def openai_call(
    prompt: str,
    model: str = OPENAI_API_MODEL,
    temperature: float = 0.5,
    max_tokens: int = 150,
):
    """
    Calls the OpenAI API to generate text based on the specified prompt and model.

    Args:
        prompt (str): The prompt to use for text generation.
        model (str): The model to use for text generation (default: OPENAI_API_MODEL).
        temperature (float): The "temperature" parameter to use for 
            text generation (default: 0.5).
        max_tokens (int): The maximum number of tokens to generate (default: 150).

    Returns:
        str: The generated text.
    """
    while True:
        try:
            if not model.startswith("gpt-"):
                # Use completion API
                response = openai.Completion.create(
                    engine=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                return response.choices[0].text.strip()
            else:
                # Use chat completion API
                messages = [{"role": "user", "content": prompt}]
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    n=1,
                    stop=None,
                )
                return response.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            print(
                "The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again."
            )
            time.sleep(10)  # Wait 10 seconds and try again
        else:
            break


def task_creation_agent(
    objective: str, result: Dict, task_description: str, task_list: List[str]
):
    """
    Generates new tasks based on the result of an execution agent 
    and a list of incomplete tasks.

    Args:
        objective (str): The objective of the new tasks.
        result (Dict): The result of the last completed task.
        task_description (str): The description of the last completed task.
        task_list (List[str]): A list of incomplete tasks.

    Returns:
        List[Dict[str, str]]: A list of dictionaries representing the 
        new tasks, each with a "task_name" key.
    """
    prompt = f"""
    You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective},
    The last completed task has the result: {result}.
    This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}.
    Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks.
    Return the tasks as an array."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]
    return [{"task_name": task_name} for task_name in new_tasks]


def prioritization_agent(this_task_id: int, objective: str, task_list: deque):
    """
    Reprioritizes the task list by cleaning its formatting and returning 
    the result as a numbered list.

    Args:
        this_task_id (int): The ID of the current task.
        objective (str): The objective of the task list.
        task_list (deque): A deque of dictionaries representing the

    Returns:
        None: This function does not return anything, but it updates the 
        `task_list` variable for the next round.
    """
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id) + 1
    prompt = f"""
    You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}.
    Consider the ultimate objective of your team:{objective}.
    Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    response = openai_call(prompt)
    new_tasks = response.split("\n")
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})


def context_agent(query: str, n: int):
    """
    Returns a list of n most relevant task metadata based on the given query.

    Args:
        query (str): The query string to search for in the task metadata.
        n (int): The number of most relevant task metadata to return.

    Returns:
        List[str]: A list of n most relevant task metadata.
    """

    query_embedding = get_ada_embedding(query)
    results = index.query(query_embedding, top_k=n, include_metadata=True)

    sorted_results = sorted(
        results.matches, key=lambda x: x.score, reverse=True)
    return [(str(item.metadata["task"])) for item in sorted_results]


def execution_agent(objective: str, task: str) -> str:
    """
    An AI agent that performs a given task based on an objective and context.

    Parameters:
    objective (str): The objective of the task.
    task (str): The task to be performed.

    Returns:
    str: The response generated by the AI agent.
    """
    context = context_agent(query=objective, n=5)
    prompt = f"""
    You are an AI who performs one task based on the following objective: {objective}\n.
    Take into account these previously completed tasks: {context}\n.
    Your task: {task}\nResponse:"""
    return openai_call(prompt, temperature=0.7, max_tokens=2000)


def textbox(text, style={
            'max-width': '100%',
            'width': 'max-content',
            'text-align': 'justify',
            'text-justify': 'inter-word',
            'font-size': '1.em',
            'font-weight': 'bold',
            'float': 'right'
            }):

    return dcc.Markdown(text, style=style)


conversation = html.Div(
    style={'width': '100%',
           'max-width': '100vw',
           'height': '70vh',
           'margin': 'auto',
           'overflow': 'auto',
           'display': 'flex',
           'flex-direction': 'column-reverse'},
    id='display-conversation',
)

inputs_fields = dbc.InputGroup(
    style={'width': '100%', 'max-width': '100vw',
           'margin': 'auto'},
    children=[
        html.Div(
            [
                dbc.Label("Number of rounds for the Tasker to run.",
                          className='modal-body-text-style'),
                dcc.Slider(1, 20, 1, value=5, marks=None, id='rounds',
                           tooltip={"placement": "top", "always_visible": True}),
                dbc.Label("Write an objective.",
                          className='modal-body-text-style'),
                dcc.Textarea(
                    id='objective',
                    value="Write an article about human-centered AI.",
                    title='''Write an objective...''',
                    style={'border-radius': '5px',
                           'margin': '1px',
                           'color': '#313638',
                           'background-color': '#f2f2f2',
                           'width': '100%',
                           'max-width': '100vw', }),
                dbc.Label("Write the first task to accomplish.",
                          className='modal-body-text-style'),
                dcc.Textarea(
                    id='first-task',
                    value="Create a skeleton for the article.",
                    title='''Write the first task to accomplish...''',
                    style={'border-radius': '5px',
                           'margin': '1px',
                           'color': '#313638',
                           'background-color': '#f2f2f2',
                           'width': '100%',
                           'max-width': '100vw', }),
            ], style={
                'width': '100%',
                'max-width': '100vw',
                'margin': 'auto',
                'background-color': 'none'}
        ),
    ],
)

controls = html.Div(
    [
        dbc.Accordion(
            [
                dbc.AccordionItem(
                    inputs_fields,
                    title=["Controls ⚙️"],
                ),
            ], start_collapsed=True, flush=False,
        ),
    ]
)

tdaa_modal = html.Div(
    [
        html.A([html.I(className='bi bi-info-circle')],
               id="open-tdaa-modal", n_clicks=0, className="icon-button", style={'font-size': 25}),
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle(dcc.Markdown(
                    '## Task-driven Autonomous Agent'), style={'font-weight': 'bold'})),
                dbc.ModalBody([
                    dcc.Markdown('''Task-Driven Autonomous Agent (`TDAA`) leverages [OpenAI’s](https://platform.openai.com/docs/models) GPT language models, [Pinecone](https://www.pinecone.io/) vector search, and the [LangChain framework](https://github.com/hwchase17/langchain) to perform a wide range of tasks across diverse domains. This application is an implementation of the [babyAGI engine](https://github.com/yoheinakajima/babyagi), (proposed by [Yohei Nakajima](https://yoheinakajima.com/)) a system capable of completing tasks, generating new tasks based on completed results, and prioritizing tasks in real-time.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''The system uses:''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''
                    - `GPT-3.5` to perform various tasks based on the given context.
                    - `Pinecone` to store and retrieve task-related data, such as task descriptions, constraints, and results.
                    - All is integrated with the `LangChain` framework to enhance the agent's capabilities, particularly in task completion and agent-based decision-making processes.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''Overall, the agent maintains a task list, represented by a double-ended queue data structure, to manage and prioritize tasks. The system autonomously creates new tasks based on completed results and reprioritized the task list accordingly. The end result is a powerful optimizer capable of solving many kinds of complex tasks.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown(
                        '''### Controls ⚙️''', style={'font-weight': 'bold'}), html.Br(),
                    dcc.Markdown(
                        '''
                        - `Rounds`: Number of times the `TDAA` repeats an execution loop (completing task, generating new tasks, prioritizing tasks).
                        - `Objective`: The goal you are trying to attain.
                        - `First Task`: An initial task to get things started.
                        ''', className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown(
                        '''### Mini-Model Card (GPT-3.5) 📄''', style={'font-weight': 'bold'}), html.Br(),
                    dcc.Markdown(
                        '''`GPT-3.5` does not have a model card with much detail, but we can use [GPT-3 model card](https://github.com/openai/gpt-3/blob/master/model-card.md) to infer some of the properties that `GPT-3.5` inherits from its predecessor.''', className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''### Details 📚''', style={
                                 'font-weight': 'bold'}), html.Br(),
                    dcc.Markdown('''
                    - Name:  [`GPT-3`](https://arxiv.org/abs/2005.14165).
                    - Model Size: 175B.
                    - Dataset: The GPT-3 [training dataset](https://github.com/openai/gpt-3/blob/master/model-card.md#data) is composed of text posted to the internet, or of text uploaded to the internet (e.g., books).
                    - Input/Output Format:  `Text`.
                    - Research Field:  `Deep Learning, Natural Language Processing`.
                    - Date of Publication: September 2020.
                    - Organization:  [OpenAI](https://openai.com/)  (Nonprofit/For-Profit).
                    - Country/Origin: United States of America.
                    - Open Source: No.
                    - Publication:  [Language Models are Few-Shot Learners](https://arxiv.org/abs/2005.14165).
                    ''', className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''### Organization 🏟️''', style={
                                 'font-weight': 'bold'}), html.Br(),
                    dcc.Markdown('''[OpenAI](https://openai.com/)  is a research institution whose mission "_is to ensure that General Artificial Intelligence (AGI) benefits all of humanity_." The organization maintains an active research and development agenda in AI Safety. Practically all models created by OpenAI are accompanied by safety reports, impact assessments, etc. Models like the  [GPT](https://arxiv.org/abs/2005.14165),  [DALL-E](https://arxiv.org/abs/2102.12092),  [Codex](https://arxiv.org/abs/2107.03374), are all accompanied by "_Broader Impacts and Hazard Analysis_".''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''OpenAI is one of the few research institutions that  [openly advocate for Humanities participation and involvement](https://openai.com/blog/ai-safety-needs-social-scientists/)  in research related to the development of safe and ethical AI.''', className='modal-body-text-style', style={
                                 'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''### Intended Use 🎯''', style={
                                 'font-weight': 'bold'}), html.Br(),
                    dcc.Markdown('''The intended direct users of `GPT-3` are developers who access its capabilities via the OpenAI API. Access and use are subject to OpenAI's access approval process, API Usage Guidelines, and API Terms of Use, which are designed to prohibit the use of the API in a way that causes societal harm.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''### Limitations ⚠️''', style={
                                 'font-weight': 'bold'}), html.Br(),
                    dcc.Markdown(
                        '''`GPT-3` has the propensity to generate text that contains falsehoods and expresses them confidently, and, like any model with ML components, it can only be expected to provide reasonable outputs when given inputs similar to the ones present in its training data. `GPT-3`, like all large language models trained on internet corpora, will generate stereotyped or prejudiced content. For a more extensive review of `GPT-3` limitations, read the "_Broader Impacts_" section on the [original paper](https://arxiv.org/abs/2005.14165) or the [model card](https://github.com/openai/gpt-3/blob/master/model-card.md#limitations).''', className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''### Risk Assessment''', style={
                                 'font-weight': 'bold'}), html.Br(),
                    dcc.Markdown('''According to this introduction [homepage](https://openai.com/blog/chatgpt/), there are several limitations related to the ChatGPT/GPT-3.5 technology, some of which are still being improved:''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''- 🤥 Generative models can perpetuate the generation of pseudo-informative content, that is, false information that may appear truthful. For example, multi-modal generative models can be used to create images with untruthful content, while language models for text generation can automate the generation of misinformation.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''- 🤬 In certain types of tasks, generative models can generate toxic and discriminatory content inspired by historical stereotypes against sensitive attributes (for example, gender, race, religion). Unfiltered public datasets may also contain inappropriate content, such as pornography, racist images, and social stereotypes, which can contribute to unethical biases in generative models. Furthermore, when prompted with non-English languages, some generative models may perform poorly.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''- 🎣 Generative models with high performance in conversational tasks can be used by malicious actors to intentionally cause harm through social engineering techniques like phishing and large-scale fraud. Also, anthropomorphizing AI models can lead to unrealistic expectations and a lack of understanding of the limitations and capabilities of the technology, which can result in potentially harmful decisions being made based on this misinformation.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''- 🐱‍💻 Code generation models have the potential to significantly accelerate malware development, enabling malicious actors to launch more sophisticated and effective cyberattacks. These tools may also help lower the intellectual/technique barrier that prevents many people from getting into black hat hacking.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''- 🏭 The development of large machine learning models can have significant environmental impacts due to the high energy consumption required for their training. If the energy used to power their training process comes from burning fossil fuels, it can contribute to the injection of large amounts of CO2 into the atmosphere. Hyperparameter optimization (often necessary before final training) can also contribute to these energy-intensive tasks.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''- 🚀 In terms of long-term AI safety, generalist and multi-task models, which are capable of carrying out a variety of tasks (moving AI development closer to Artificial General Intelligence), may present unknown risks. Additionally, models that have programming abilities could be dangerous because they could enable AI systems to modify or rewrite their source code.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''- 👷 A significant portion of the workforce today still performs many tasks that can be automated using generative models. In some industries, these models might provoke considerable labor displacement.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                    dcc.Markdown('''- 👨‍🎓 Generative models can automate the process of academic writing and creation. This could have an impact on how educational institutions assess the learning of their students. Dishonest students could use such models to completely automate their tasks instead of using them as augmenting tools.''',
                                 className='modal-body-text-style', style={'font-size': FONT_SIZE}), html.Br(),
                ]),
                dbc.ModalFooter(
                    dbc.Button(
                        html.I(className="bi bi-x-circle"),
                        id='close-tdaa-modal',
                        className='ms-auto',
                        outline=True,
                        size='xl',
                        n_clicks=0,
                        color=CLOSE_BUTTON,
                        style=STYLE_BUTTON
                    )
                ),
            ],
            id='tdaa-modal',
            scrollable=True,
            fullscreen=True,
            is_open=False,
        ),
    ], style={
        'margin-top': '5px',
        'margin-left': '15px',
    },

)


def toggle_modal(n1, n2, is_open):
    """
    Toggles the visibility of the simple modal window.

    Args:
    ---------
        n1 (bool): A flag to check if the first modal is open or closed.
        n2 (bool): A flag to check if the second modal is open or closed.
        is_open (bool): A flag to check if the modal is currently open or not.

    Returns:
    ---------
        bool: The updated value of the `is_open` flag after toggling the modal window.
    """
    if n1 or n2:
        return not is_open
    return is_open


badges = html.Span([
    dbc.Badge([html.I(className="bi bi-heart-fill"), "  Open-Source"], href="https://github.com/Nkluge-correa/",
              color="dark", className="text-decoration-none", style={'margin-right': '5px'}),
    dbc.Badge([html.I(className="bi bi-filetype-py"), "  Made with Python"], href="https://www.python.org/",
              color="dark", className="text-decoration-none", style={'margin-right': '5px'}),
])
