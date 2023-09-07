from skills.skill import Skill
import openai
import litellm

class TextCompletion(Skill):
    name = 'text_completion'
    description = "A tool that uses OpenAI's text completion API to generate, summarize, and/or analyze text and code."
    api_keys_required = ['openai']

    def __init__(self, api_keys):
        super().__init__(api_keys)

    def execute(self, params, dependent_task_outputs, objective):
        if not self.valid:
            return
        
        task_prompt = f"Complete your assigned task based on the objective and only based on information provided in the dependent task output, if provided. \n###\nYour objective: {objective}. \n###\nYour task: {params} \n###\nDependent tasks output: {dependent_task_outputs}  \n###\nYour task: {params}\n###\nRESPONSE:"
      
        messages = [
            {"role": "user", "content": task_prompt}
        ]
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.4,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
    
        return "\n\n"+response.choices[0].message['content'].strip()
