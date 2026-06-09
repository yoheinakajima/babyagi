import requests

class Agent:
    def __init__(self):
        self.capabilities = ["task_execution", "data_research", "bounty_solving"]
        self.languages = ["en"]
        self.display_name = "BabyAGI"
        self.manifest_url = "https://raw.githubusercontent.com/yoheinakajima/babyagi/main/README.md"

    def register(self):
        response = requests.post(
            "https://kjtirbnxxymeumycrhqv.supabase.co/functions/v1/runtime-public-federation/register",
            json={
                "manifest_url": self.manifest_url,
                "display_name": self.display_name,
                "capabilities": self.capabilities,
                "languages": self.languages
            }
        )
        return response

# Create an instance of the Agent class and call the register method
agent = Agent()
response = agent.register()
print(response.text)