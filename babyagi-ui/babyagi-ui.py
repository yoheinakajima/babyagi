from dash import dcc, html, Output, Input, State
import dash_bootstrap_components as dbc
from collections import deque
import dash

from babyagi_elements import OPENAI_API_MODEL, index, execution_agent
from babyagi_elements import task_creation_agent, prioritization_agent, get_ada_embedding
from babyagi_elements import textbox, conversation, controls, tdaa_modal, toggle_modal, badges


app = dash.Dash(__name__,
                meta_tags=[
                    {'name': 'viewport', 'content': 'width=device-width, initial-scale=1.0, maximum-scale=1.2, minimum-scale=0.5,'}],
                external_stylesheets=[dbc.themes.SLATE, dbc.icons.BOOTSTRAP])

server = app.server
app.title = 'TADD 📝'


app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row([
            dbc.Col([
                html.Div([dcc.Markdown('# `Task-driven Autonomous Agent`', className='title-style'),
                          html.Img(src=dash.get_asset_url(
                              'task.gif'), height="80px", className='title-icon-style')],
                    className='title-div'),
                html.Div([
                    html.Div([
                        dcc.Markdown('''
                TDAA is an example of an AI-powered task management system, capable of creating, prioritizing, and executing tasks given a predefined objective.
                ''', className='page-intro')
                    ], className='page-intro-inner-div'),
                ], className='page-intro-outer-div'),
                html.Div([tdaa_modal], className='middle-toggles'),
                html.Div([controls], style={'margin-bottom': '5px'}),
                dbc.Button(
                    [html.I(className="bi bi-send")], size='lg', id='submit',
                    outline=True, color='light', style={
                        'border-radius': '5px',
                        'margin': '2px',
                        'width': '100%',
                        'max-width': '100vw',
                        'background-color': 'none'}),
                dcc.Loading(id='loading_0', type='circle',
                            color="#dc3d87",
                            children=[conversation]),
                html.Div([
                    html.Div([badges], className='badges'),
                ], className='badges-div'),
                dcc.Store(id='store-conversation', data=''),
            ], width=12)
        ], justify='center'),
    ],
)


@app.callback(
    Output('display-conversation', 'children'),
    [Input('store-conversation', 'data')]

)
def update_display(chat_history):
    return [
        textbox(message)
        for message in chat_history
    ]


@app.callback(
    [
        Output('store-conversation', 'data'),
        Output('display-conversation', 'key')
    ],

    [
        Input('submit', 'n_clicks'),
    ],

    [
        State('objective', 'value'),
        State('first-task', 'value'),
        State('rounds', 'value'),
        State('store-conversation', 'data'),
    ], prevent_initial_call=True
)
def run_chatbot(n_clicks, objective, task, rounds, chat_history):
    """
    A function that simulates a task management agent that can manage tasks, 
    solve them, and create new tasks based on the results.

    Args:
        n_clicks (int): The number of times the function has been clicked.
        objective (str): The overall objective or goal that the task 
            management agent is trying to achieve.
        task (str): The initial task that the agent needs to complete to 
            achieve the objective.
        rounds (int): The number of rounds of task management that the agent will perform.
        chat_history (list[str]): A list of chat messages containing the task management 
            agent's conversation history.

    Returns:
        tuple: A tuple containing the updated chat history (list of strings) 
            and an empty string (to clear the input field).
    """
    chat_history = chat_history or []
    if n_clicks == 0:
        raise dash.exceptions.PreventUpdate

    if objective is None or objective == '' or task is None or task == '':
        raise dash.exceptions.PreventUpdate

    if objective is None or objective.isspace() is True or task is None or task.isspace() is True:
        raise dash.exceptions.PreventUpdate

    else:
        chat_history.insert(0, f'`Objective:` {objective}')
        chat_history.insert(0, f'`Task:` {task}')
        chat_history.insert(
            0, f"`USING {OPENAI_API_MODEL.upper()} AS A TASK MANAGEMENT AGENT.`")

        task_id_counter = 1
        first_task = {"task_id": 1, "task_name": task}
        task_list = deque([])
        task_list.append(first_task)

        for i in range(rounds):
            if task_list:

                chat_history.insert(0, f'`Current Task List`:')
                for t in task_list:
                    chat_history.insert(
                        0, f"""- `Task Name`: {t["task_name"]}""")

                # Step 1: Pull the first task
                print('Pulling the first task...')
                task = task_list.popleft()
                chat_history.insert(0, f"""`Next Task`: {task["task_name"]}""")

                # Send to execution function to complete the task based on the context
                print('Solving selected task...')
                result = execution_agent(objective, task["task_name"])
                this_task_id = int(task["task_id"])
                chat_history.insert(0, f"""`Task Result`: {result}""")

                # Step 2: Enrich result and store in Pinecone
                print('Enriching result and storing in Pinecone...')
                enriched_result = {
                    "data": result
                }  # This is where you should enrich the result if needed
                result_id = f"result_{task['task_id']}"
                vector = get_ada_embedding(
                    enriched_result["data"]
                )  # get vector of the actual result extracted from the dictionary
                index.upsert(
                    [(result_id, vector, {
                        "task": task["task_name"], "result": result})]
                )

                # Step 3: Create new tasks and reprioritize task list
                print('Creating new tasks and reprioritizing task list...')
                new_tasks = task_creation_agent(
                    objective,
                    enriched_result,
                    task["task_name"],
                    [t["task_name"] for t in task_list],
                )

                for new_task in new_tasks:
                    task_id_counter += 1
                    new_task.update({"task_id": task_id_counter})
                    task_list.append(new_task)
                prioritization_agent(this_task_id, objective, task_list)

        return chat_history, ''


app.callback(
    Output('tdaa-modal', 'is_open'),
    [
        Input('open-tdaa-modal', 'n_clicks'),
        Input('close-tdaa-modal', 'n_clicks'),
    ],
    [State('tdaa-modal', 'is_open')],
)(toggle_modal)


if __name__ == '__main__':
    app.run_server(debug=True)
