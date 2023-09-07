from skills.skill import Skill
import openai
import litellm

#This is an experimental skill to have BabyAGI use BabyAGI as a skill, which really isnt necessary, and also buggy.
class CallBabyagi(Skill):
    name = 'call_babyagi'
    description = 'A skill that rewrites a task description into an objective, and sends it to itself (an autonomous agent) to complete. Helpful for research.'
    api_keys_required = [['openai']]

    def __init__(self, api_keys, main_loop_function):
        super().__init__(api_keys, main_loop_function)

    def execute(self, params, dependent_task_outputs, objective):
        # Generate the new objective by rewriting the task description
        new_objective = self.generate_new_objective(params)

        LOAD_SKILLS = ['web_search','text_completion']
        # Send the new objective to the main loop
        result = self.main_loop_function(new_objective, LOAD_SKILLS, self.api_keys, False)

        # Return the main loop's output as the result of the skill
        return result


    def generate_new_objective(self, task_description):
        prompt = f"You are an AI assistant tasked with rewriting the following task description into an objective, and remove any mention of call_babyagi: {task_description}\nObjective:"

        messages = [
            {"role": "user", "content": prompt}
        ]
        response = litellm.completion(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return response.choices[0].message['content'].strip()
