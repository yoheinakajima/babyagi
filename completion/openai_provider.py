import openai
import os
import backoff

class OpenAiProvider:
    def __init__(self, api_key=None, engine="text-davinci-002", max_tokens=1024):
        if api_key is None:
            api_key = os.environ.get("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("API key not provided and OPENAI_API_KEY environment variable not set")
        openai.api_key = api_key
        self.engine = engine
        self.max_tokens = max_tokens
        

    @backoff.on_exception(backoff.expo, openai.error.RateLimitError, max_time=300, max_tries=8)
    def completions_with_backoff(self, **kwargs):
        return openai.ChatCompletion.create(**kwargs)
    
    def generate_text(self, prompt, temperature=0.3):
        messages = [{"role": "user", "content": prompt}]
        try:
            
            completions = self.completions_with_backoff(
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=temperature,
                max_tokens=self.max_tokens,
                n=1,
                stop=None,
            )
            
            # Access the generated text
            generated_text = completions["choices"][0]["message"]["content"]
            return generated_text
    
        except Exception as e:
            print(f"An error occurred: {e}")
            return ''
