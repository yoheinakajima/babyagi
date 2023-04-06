import openai

class OpenAIHelper:
    def __init__() -> None:
        pass

    def get_davinci_response(prompt: str):
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.7,
            max_tokens=2000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].text.strip()

    def get_ada_embedding(text):
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]