from abc import ABC, abstractmethod

class CompletionClient(ABC):
    @abstractmethod
    def text_completion(self, prompt: str, temperature: float = 0.5, max_tokens: int = 100) -> str:
        pass


def get_completion_client(api_key: str, model: str) -> CompletionClient:
    if "davinci" in model.lower():
        from .openai_davinci import DavinciClient
        return DavinciClient(api_key, model)
    elif "gpt" in model.lower():
        from .openai_gpt import GptClient
        return GptClient(api_key, model)
    else:
        from .openai_davinci import DavinciClient
        return DavinciClient(api_key)