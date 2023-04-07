from .ICompletionClient import CompletionClient
import openai

class DavinciClient(CompletionClient):
    def __init__(self, api_key: str, engine: str = "text-davinci-003"):
        openai.api_key = api_key
        self.engine = engine

    def text_completion(self, prompt, temperature: float = 0.5, max_tokens: int = 100) -> str:
        response = openai.Completion.create(
            engine=self.engine,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].text.strip()