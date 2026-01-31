from skills.skill import Skill
import os
import openai

class ObjectiveSaver(Skill):
    name = 'objective_saver'
    description = "A skill that saves a new example_objective based on the concepts from skill_saver.py"
    api_keys_required = []

    def __init__(self, api_keys):
        super().__init__(api_keys)

    def execute(self, params, dependent_task_outputs, objective):
        if not self.valid:
            return
        #print(dependent_task_outputs[2])
        code =  dependent_task_outputs[2]
        task_prompt = f"Come up with a file name (eg. 'research_shoes.json') for the following objective:{code}\n###\nFILE_NAME:"
      
        messages = [
            {"role": "user", "content": task_prompt}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.4,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        ) 
    
        file_name =  response.choices[0].message['content'].strip()
        file_path = os.path.join('tasks/example_objectives',file_name)

        try:
            with open(file_path, 'w') as file:
                file.write("["+code+"]")
                print(f"Code saved successfully: {file_name}")
        except:
            print("Error saving code.")

        return None