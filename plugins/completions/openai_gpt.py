from .ICompletionClient import CompletionClient
import openai

class GptClient(CompletionClient):
    def __init__(self, api_key: str, model: str = 'gpt-35-turbo'):
        print(f"\033[91m\033[1m\n*****USING {model.upper()}. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****\033[0m\033[0m")
        openai.api_key = api_key
        self.model = model

    def text_completion(self, prompt: str, temperature: float = 0.5, max_tokens: int = 100) -> str:
        messages = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model=self.model,
            messages = messages,
            temperature = temperature,
            max_tokens = max_tokens,
            n=1,
            stop=None,
        )
        return response.choices[0].message.content.strip()