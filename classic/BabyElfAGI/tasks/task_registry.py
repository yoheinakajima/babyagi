import openai
import litellm
import json
import threading
import os
import numpy as np

class TaskRegistry:
    def __init__(self):
        self.tasks = []
        # Initialize the lock
        self.lock = threading.Lock()
        objectives_file_path = "tasks/example_objectives"
        self.example_loader = ExampleObjectivesLoader(objectives_file_path)

    def load_example_objectives(self, user_objective):
        return self.example_loader.load_example_objectives(user_objective)

      
    def create_tasklist(self, objective, skill_descriptions):
        #load most relevant object and tasklist from objectives_examples.json
        example_objective, example_tasklist = self.load_example_objectives(objective)

        prompt = (
            f"You are an expert task list creation AI tasked with creating a  list of tasks as a JSON array, considering the ultimate objective of your team: {objective}. "
            f"Create a very short task list based on the objective, the final output of the last task will be provided back to the user. Limit tasks types to those that can be completed with the available skills listed below. Task description should be detailed.###"
            f"AVAILABLE SKILLS: {skill_descriptions}.###"
            f"RULES:"
            f"Do not use skills that are not listed."
            f"Always include one skill."
            f"dependent_task_ids should always be an empty array, or an array of numbers representing the task ID it should pull results from."
            f"Make sure all task IDs are in chronological order.###\n"
            f"EXAMPLE OBJECTIVE={json.dumps(example_objective)}"
            f"TASK LIST={json.dumps(example_tasklist)}"
            f"OBJECTIVE={objective}"
            f"TASK LIST="
        )

        print("\033[90m\033[3m" + "\nInitializing...\n" + "\033[0m")
        response = litellm.completion(
            model="gpt-3.5-turbo-0613",
            messages=[
                {
                    "role": "system",
                    "content": "You are a task creation AI."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=1500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        # Extract the content of the assistant's response and parse it as JSON
        result = response["choices"][0]["message"]["content"]
        try:
            task_list = json.loads(result)
            self.tasks = task_list
        except Exception as error:
            print(error)


    def execute_task(self, i, task, skill_registry, task_outputs, objective):
        p_nexttask="\033[92m\033[1m"+"\n*****NEXT TASK ID:"+str(task['id'])+"*****\n"+"\033[0m\033[0m"
        p_nexttask += f"\033[ EExecuting task {task.get('id')}: {task.get('task')}) [{task.get('skill')}]\033[)"
        print(p_nexttask)
        # Retrieve the skill from the registry
        skill = skill_registry.get_skill(task['skill'])
        # Get the outputs of the dependent tasks
        dependent_task_outputs = {dep: task_outputs[dep]["output"] for dep in task['dependent_task_ids']} if 'dependent_task_ids' in task else {}
        # Execute the skill
        # print("execute:"+str([task['task'], dependent_task_outputs, objective]))
        task_output = skill.execute(task['task'], dependent_task_outputs, objective)
        print("\033[93m\033[1m"+"\nTask Output (ID:"+str(task['id'])+"):"+"\033[0m\033[0m")
        print("TASK: "+str(task["task"]))
        print("OUTPUT: "+str(task_output))
        return i, task_output

  
    def reorder_tasks(self):
        self.tasks = sorted(self.tasks, key=lambda task: task['id'])

  
    def add_task(self, task, after_task_id):
        # Get the task ids
        task_ids = [t["id"] for t in self.tasks]

        # Get the index of the task id to add the new task after
        insert_index = task_ids.index(after_task_id) + 1 if after_task_id in task_ids else len(task_ids)

        # Insert the new task
        self.tasks.insert(insert_index, task)
        self.reorder_tasks()


    def update_tasks(self, task_update):
        for task in self.tasks:
            if task['id'] == task_update['id']:
                # This merges the original task dictionary with the update, overwriting only the fields present in the update.
                task.update(task_update)
                self.reorder_tasks()

    def reflect_on_output(self, task_output, skill_descriptions):
        with self.lock:
            example = [
                [
                    {"id": 3, "task": "New task 1 description", "skill": "text_completion_skill",
                     "dependent_task_ids": [], "status": "complete"},
                    {"id": 4, "task": "New task 2 description", "skill": "text_completion_skill",
                     "dependent_task_ids": [], "status": "incomplete"}
                ],
                [2, 3],
                {"id": 5, "task": "Complete the objective and provide a final report",
                 "skill": "text_completion_skill", "dependent_task_ids": [1, 2, 3, 4], "status": "incomplete"}
            ]

            prompt = (
                f"You are an expert task manager, review the task output to decide at least one new task to add."
                f"As you add a new task, see if there are any tasks that need to be updated (such as updating dependencies)."
                f"Use the current task list as reference."
                f"Do not add duplicate tasks to those in the current task list."
                f"Only provide JSON as your response without further comments."
                f"Every new and updated task must include all variables, even they are empty array."
                f"Dependent IDs must be smaller than the ID of the task."
                f"New tasks IDs should be no larger than the last task ID."
                f"Always select at least one skill."
                f"Task IDs should be unique and in chronological order."                f"Do not change the status of complete tasks."
                f"Only add skills from the AVAILABLE SKILLS, using the exact same spelling."
                f"Provide your array as a JSON array with double quotes. The first object is new tasks to add as a JSON array, the second array lists the ID numbers where the new tasks should be added after (number of ID numbers matches array), and the third object provides the tasks that need to be updated."
                f"Make sure to keep dependent_task_ids key, even if an empty array."
                f"AVAILABLE SKILLS: {skill_descriptions}.###"
                f"\n###Here is the last task output: {task_output}"
                f"\n###Here is the current task list: {self.tasks}"
                f"\n###EXAMPLE OUTPUT FORMAT = {json.dumps(example)}"
                f"\n###OUTPUT = "
            )
            print("\033[90m\033[3m" + "\nReflecting on task output to generate new tasks if necessary...\n" + "\033[0m")
            response = litellm.completion(
                model="gpt-3.5-turbo-16k-0613",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a task creation AI."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=1500,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )

            # Extract the content of the assistant's response and parse it as JSON
            result = response["choices"][0]["message"]["content"]
            print("\n#" + str(result))

            # Check if the returned result has the expected structure
            if isinstance(result, str):
                try:
                    task_list = json.loads(result)
                    # print("RESULT:")

                    print(task_list)
                    # return [],[],[]
                    return task_list[0], task_list[1], task_list[2]
                except Exception as error:
                    print(error)

            else:
                raise ValueError("Invalid task list structure in the output")

    def get_tasks(self):
        """
        Returns the current list of tasks.

        Returns:
        list: the list of tasks.
        """
        return self.tasks

    def get_task(self, task_id):
        """
        Returns a task given its task_id.

        Parameters:
        task_id : int
            The unique ID of the task.

        Returns:
        dict
            The task that matches the task_id.
        """
        matching_tasks = [task for task in self.tasks if task["id"] == task_id]

        if matching_tasks:
            return matching_tasks[0]
        else:
            print(f"No task found with id {task_id}")
            return None

    def print_tasklist(self, task_list):
        p_tasklist="\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m"
        for t in task_list:
            dependent_task_ids = t.get('dependent_task_ids', [])
            dependent_task = ""
            if dependent_task_ids:
                dependent_task = f"\033[31m<dependencies: {', '.join([f'#{dep_id}' for dep_id in dependent_task_ids])}>\033[0m"
            status_color = "\033[32m" if t.get('status') == "completed" else "\033[31m"
            p_tasklist+= f"\033[1m{t.get('id')}\033[0m: {t.get('task')} {status_color}[{t.get('status')}]\033[0m \033[93m[{t.get('skill')}] {dependent_task}\033[0m\n"
        print(p_tasklist)



class ExampleObjectivesLoader:
    def __init__(self, objectives_folder_path):
        self.objectives_folder_path = objectives_folder_path
        self.objectives_examples = []  # Initialize as an empty list

    def load_objectives_examples(self):
        self.objectives_examples = []
        for filename in os.listdir(self.objectives_folder_path):
            file_path = os.path.join(self.objectives_folder_path, filename)
            with open(file_path, 'r') as file:
                objectives = json.load(file)
                self.objectives_examples.extend(objectives)
    

    def find_most_relevant_objective(self, user_input):
        user_input_embedding = self.get_embedding(user_input, model='text-embedding-ada-002')
        most_relevant_objective = max(
            self.objectives_examples,
            key=lambda pair: self.cosine_similarity(pair['objective'], user_input_embedding)
        )
        return most_relevant_objective['objective'], most_relevant_objective['examples']


    def get_embedding(self, text, model='text-embedding-ada-002'):
        response = openai.Embedding.create(input=[text], model=model)
        embedding = response['data'][0]['embedding']
        return embedding

    def cosine_similarity(self, objective, embedding):
        max_similarity = float('-inf')
        objective_embedding = self.get_embedding(objective, model='text-embedding-ada-002')
        similarity = self.calculate_similarity(objective_embedding, embedding)
        max_similarity = max(max_similarity, similarity)
        return max_similarity

    def calculate_similarity(self, embedding1, embedding2):
        embedding1 = np.array(embedding1, dtype=np.float32)
        embedding2 = np.array(embedding2, dtype=np.float32)
        similarity = np.dot(embedding1, embedding2) / (np.linalg.norm(embedding1) * np.linalg.norm(embedding2))
        return similarity

    def load_example_objectives(self, user_objective):
        self.load_objectives_examples()
        most_relevant_objective, most_relevant_tasklist = self.find_most_relevant_objective(user_objective)
        example_objective = most_relevant_objective
        example_tasklist = most_relevant_tasklist
        return example_objective, example_tasklist
    