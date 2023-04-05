class BaseAgent:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def __call__(self, **kwargs) -> str:
        prompt = self.config["prompt"].format(**kwargs)
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=self.config.get("temperature", 0.5),
            max_tokens=self.config.get("max_tokens", 1000),
            top_p=self.config.get("top_p", 1),
            frequency_penalty=self.config.get("frequency_penalty", 0),
            presence_penalty=self.config.get("presence_penalty", 0)
        )
        return response.choices[0].text.strip()
