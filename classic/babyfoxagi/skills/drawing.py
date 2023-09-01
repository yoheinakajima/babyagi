from skills.skill import Skill
import openai

class Drawing(Skill):
    name = 'drawing'
    description = "A tool that draws on an HTML canvas using OpenAI."
    api_keys_required = ['openai']

    def __init__(self, api_keys, main_loop_function):
        super().__init__(api_keys, main_loop_function)

    def execute(self, params, dependent_task_outputs, objective):
        if not self.valid:
            return
        
        task_prompt = f"Do a detailed HTML canvas drawing of the user request: {params}. Start with <canvas> and end with </canvas>. Only provide code.:"
      
        messages = [
            {"role": "user", "content": task_prompt}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo-16k",
            messages=messages,
            temperature=0.4,
            max_tokens=4000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
    
        return "\n\n"+response.choices[0].message['content'].strip()
