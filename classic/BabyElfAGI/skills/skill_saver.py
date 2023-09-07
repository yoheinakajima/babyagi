from skills.skill import Skill
import os
import openai
import litellm

class SkillSaver(Skill):
    name = 'skill_saver'
    description = "A skill that saves code written in a previous step into a file within the skills folder. Not for writing code."
    api_keys_required = []

    def __init__(self, api_keys):
        super().__init__(api_keys)

    def execute(self, params, dependent_task_outputs, objective):
        if not self.valid:
            return

        task_prompt = f"Extract the code and only the code from the dependent task output here: {dependent_task_outputs}  \n###\nCODE:"
      
        messages = [
            {"role": "user", "content": task_prompt}
        ]
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.4,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        ) 
    
        code =  response.choices[0].message['content'].strip()
        task_prompt = f"Come up with a file name (eg. 'get_weather.py') for the following skill:{code}\n###\nFILE_NAME:"
      
        messages = [
            {"role": "user", "content": task_prompt}
        ]
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.4,
            max_tokens=3000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        ) 
    
        file_name =  response.choices[0].message['content'].strip()
        file_path = os.path.join('skills',file_name)

        try:
            with open(file_path, 'w') as file:
                file.write(code)
                print(f"Code saved successfully: {file_name}")
        except:
            print("Error saving code.")

        return None