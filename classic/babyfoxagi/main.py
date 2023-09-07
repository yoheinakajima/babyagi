from flask import Flask, render_template, request, jsonify, send_from_directory
import openai
import os
import json
import threading
from babyagi import get_skills, execute_skill, execute_task_list, api_keys, LOAD_SKILLS
from ongoing_tasks import ongoing_tasks

app = Flask(__name__, static_folder='public/static')
openai.api_key = os.getenv('OPENAI_API_KEY')


@app.route('/')
def hello_world():

  return render_template('index.html')


FOREVER_CACHE_FILE = "forever_cache.ndjson"
OVERALL_SUMMARY_FILE = "overall_summary.ndjson"


@app.route('/get-all-messages', methods=["GET"])
def get_all_messages():
  try:
    messages = []
    with open("forever_cache.ndjson", "r") as file:
      for line in file:
        messages.append(json.loads(line))

    return jsonify(messages)

  except Exception as e:
    return jsonify({"error": str(e)}), 500


def get_latest_summary():
  with open(OVERALL_SUMMARY_FILE, 'r') as file:
    lines = file.readlines()
  if lines:
    return json.loads(lines[-1])["summary"]  # Return the latest summary
  return ""


def summarize_text(text):
  system_message = (
    "Your task is to generate a concise summary for the provided conversation, this will be fed to a separate AI call as context to generate responses for future user queries."
    " The conversation contains various messages that have been exchanged between participants."
    " Please ensure your summary captures the main points and context of the conversation without being too verbose."
    " The summary should be limited to a maximum of 500 tokens."
    " Here's the conversation you need to summarize:")

  completion = openai.ChatCompletion.create(model="gpt-3.5-turbo-16k",
                                            messages=[{
                                              "role": "system",
                                              "content": system_message
                                            }, {
                                              "role": "user",
                                              "content": text
                                            }])

  # Extracting the content from the assistant's message
  return completion.choices[0]['message']['content'].strip()


def combine_summaries(overall, latest):
  system_message = (
    "Your task is to generate a concise summary for the provided conversation, this will be fed to a separate AI call as context to generate responses for future user queries."
    "You will do this by combining two given summaries into one cohesive summary."
    " Make sure to retain the key points from both summaries and create a concise, unified summary."
    " The combined summary should not exceed 500 tokens."
    " Here are the summaries you need to combine:")

  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-16k",
    messages=[{
      "role": "system",
      "content": system_message
    }, {
      "role":
      "user",
      "content":
      f"Overall summary: {overall}\nLatest summary: {latest}"
    }])

  # Extracting the content from the assistant's message
  return completion.choices[0]['message']['content'].strip()



def openai_function_call(user_message):
  global ongoing_tasks
  global global_skill_registry
  global_skill_registry = LOAD_SKILLS
  print("Returning GLOBAL SKILL REGISTRY")
  print(global_skill_registry)
  
  # Append the new user message to the forever_cache file
  user_entry = {"role": "user", "content": user_message}
  append_to_ndjson(FOREVER_CACHE_FILE, user_entry)

  # Retrieve the last 20 stored messages
  with open(FOREVER_CACHE_FILE, "r") as file:
    lines = file.readlines()

  last_20_messages = [json.loads(line) for line in lines][-20:]

  # Always update the summary in a separate thread
  threading.Thread(target=update_summary, args=(last_20_messages, )).start()

  overall_summary = get_latest_summary()
  print("LOAD_SKILLS")
  print(global_skill_registry)
  system_message = (
    f"You are a fun happy and quirky AI chat assistant that uses Gen Z language and lots of emojis named BabyAGI with capabilities beyond chat. For every user message, you quickly analyze whether this is a request that you can simply respond via ChatCompletion, whether you need to use one of the skills provided, or whether you should create a task list and chain multiple skills together. You will always provide a message_to_user. If path is Skill or TaskList, always generate an objective. If path is Skill, ALWAYS include skill_used from one of the available skills. ###Here are your available skills: {global_skill_registry}.###For context, here is the overall summary of the chat: {overall_summary}."
  )

  completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo-16k",
    messages=[
      {"role": "system","content": system_message},
      *last_20_messages,
      {"role": "user","content": user_message},
    ],
    functions=[{
      "name": "determine_response_type",
      "description":
      "Determine whether to respond via ChatCompletion, use a skill, or create a task list. Always provide a message_to_user.",
      "parameters": {
        "type": "object",
        "properties": {
          "message_to_user": {
            "type":
            "string",
            "description":
            "A message for the user, indicating the AI's action or providing the direct chat response. ALWAYS REQUIRED. Do not use line breaks."
          },
          "path": {
            "type":
            "string",
            "enum": ["ChatCompletion", "Skill", "TaskList"],  # Restrict the values to these three options
            "description":
            "The type of response – either 'ChatCompletion', 'Skill', or 'TaskList'"
          },
          "skill_used": {
            "type":
            "string",
            "description":
            f"If path is 'Skill', indicates which skill to use. If path is 'Skill', ALWAYS use skill_used. Must be one of these: {global_skill_registry}"
          },
          "objective": {
            "type":
            "string",
            "description":
            "If path is 'Skill' or 'TaskList', describes the main task or objective. Always include if path is 'Skill' or 'TaskList'."
          }
        },
        "required": ["path", "message_to_user", "objective", "skill_used"]
      }
    }],
    function_call={"name": "determine_response_type"})

  # Extract AI's structured response from function call
  response_data = completion.choices[0]['message']['function_call'][
    'arguments']
  if isinstance(response_data, str):
    response_data = json.loads(response_data)
  print("RESPONSE DATA:")
  print(response_data)
  path = response_data.get("path")
  skill_used = response_data.get("skill_used")
  objective = response_data.get("objective")
  task_id = generate_task_id()
  response_data["taskId"] = task_id
  if path == "Skill":
      ongoing_tasks[task_id] = {
          'status': 'ongoing',
          'description': objective,
          'skill_used': skill_used
      }
      threading.Thread(target=execute_skill, args=(skill_used, objective, task_id)).start()
      update_ongoing_tasks_file()
  elif path == "TaskList":
      ongoing_tasks[task_id] = {
          'status': 'ongoing',
          'description': objective,
          'skill_used': 'Multiple'
      }
      threading.Thread(target=execute_task_list, args=(objective, api_keys, task_id)).start()
      update_ongoing_tasks_file()

  return response_data


def generate_task_id():
  """Generates a unique task ID"""
  return f"{str(len(ongoing_tasks) + 1)}"


def update_summary(messages):
  # Combine messages to form text and summarize
  messages_text = " ".join([msg['content'] for msg in messages])
  latest_summary = summarize_text(messages_text)

  # Update overall summary
  overall = get_latest_summary()
  combined_summary = combine_summaries(overall, latest_summary)
  append_to_ndjson(OVERALL_SUMMARY_FILE, {"summary": combined_summary})


@app.route('/determine-response', methods=["POST"])
def determine_response():
  try:
    # Ensure that the request contains JSON data
    if not request.is_json:
      return jsonify({"error": "Expected JSON data"}), 400

    user_message = request.json.get("user_message")

    # Check if user_message is provided
    if not user_message:
      return jsonify({"error": "user_message field is required"}), 400

    response_data = openai_function_call(user_message)

    data = {
      "message": response_data['message_to_user'],
      "skill_used": response_data.get('skill_used', None),
      "objective": response_data.get('objective', None),
      "task_list": response_data.get('task_list', []),
      "path": response_data.get('path', []),
      "task_id": response_data.get('taskId')
    }

    # Storing AI's response to NDJSON file
    ai_entry = {
      "role": "assistant",
      "content": response_data['message_to_user']
    }
    append_to_ndjson("forever_cache.ndjson", ai_entry)

    print("END OF DETERMINE-RESPONSE. PRINTING 'DATA'")
    print(data)
    return jsonify(data)

  except Exception as e:
    print(f"Exception occurred: {str(e)}")
    return jsonify({"error": str(e)}), 500


def append_to_ndjson(filename, data):
  try:
    print(f"Appending to {filename} with data: {data}")
    with open(filename, 'a') as file:
      file.write(json.dumps(data) + '\n')
  except Exception as e:
    print(f"Error in append_to_ndjson: {str(e)}")



@app.route('/check-task-status/<task_id>', methods=["GET"])
def check_task_status(task_id):
    global ongoing_tasks
    update_ongoing_tasks_file()
    print("CHECK_TASK_STATUS")
    print(task_id)
    task = ongoing_tasks.get(task_id)

    # First check if task is None
    if not task:
        return jsonify({"error": f"No task with ID {task_id} found."}), 404

    # Now, it's safe to access attributes of task
    print(task.get("status"))
    return jsonify({"status": task.get("status")})


@app.route('/fetch-task-output/<task_id>', methods=["GET"])
def fetch_task_output(task_id):
  print("FETCH_TASK_STATUS")
  print(task_id)
  task = ongoing_tasks.get(task_id)
  if not task:
    return jsonify({"error": f"No task with ID {task_id} found."}), 404
  return jsonify({"output": task.get("output")})


def update_ongoing_tasks_file():
    with open("ongoing_tasks.py", "w") as file:
        file.write(f"ongoing_tasks = {ongoing_tasks}\n")

@app.route('/get-all-tasks', methods=['GET'])
def get_all_tasks():
    tasks = []
    for task_id, task_data in ongoing_tasks.items():
        task = {
            'task_id': task_id,
            'status': task_data.get('status', 'unknown'),
            'description': task_data.get('description', 'N/A'),
            'skill_used': task_data.get('skill_used', 'N/A'),
            'output': task_data.get('output', 'N/A')
        }
        tasks.append(task)
    return jsonify(tasks)



if __name__ == "__main__":
  app.run(host='0.0.0.0', port=8080)
