import openai
import os

class OpenAIHelper:
    def __init__(self):
        # Select the model on init
        # TODO: We shouldn't be pulling the model from the environment all the time, not efficient
        if os.environ.get("USE_GPT4", ""):
            self.engine = "gpt4"
        else:
            self.engine = "davinci"

    def get_model_response(self, prompt: str, temperature: float = 0.5, max_tokens: int = 100):
        if self.engine == "gpt4":
            return self.get_gpt4_response(prompt=prompt, temperature=temperature, max_tokens=max_tokens)
        else:
            return self.get_davinci_response(prompt=prompt, temperature=temperature, max_tokens=max_tokens)

    def get_davinci_response(self, prompt: str, temperature: float = 0.5, max_tokens: int = 100):
        # Call GPT-3 Davinci model
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].text.strip()
    
    def get_gpt4_response(self, prompt: str, temperature: float = 0.5, max_tokens: int = 100):
        # Call GPT-4 chat model
        messages=[{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages = messages,
            temperature=temperature,
            max_tokens=max_tokens,
            n=1,
            stop=None,
        )
        return response.choices[0].message.content.strip()

    def get_ada_embedding(self, text: str):
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]