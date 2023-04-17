from agents.IAgent import AgentData
from agents.scrapper_agent import ScrapperAgent
from apis.api_dispatcher import APIDispatcher
from hugging.hugging_dipatcher import HuggingDispatcher


class DispatcherAgent:
    def __init__(self, name, agent_data: AgentData):
        self.name = name
        self.api_dispatcher = None
        self.hugging_dispatcher = None
        self.openai = None
        self.browser = None
        self.scraper = None

        if name in ["wikipedia", "yelp", "arxiv", "nhanes", 'openweather', "jsonplaceholder", "pubmed", "newsapi", "clinicaltrials"]:
            self.api_dispatcher = APIDispatcher(name)
        elif name in ["bert", "chart", "transformerxl"]:
            self.hugging_dispatcher = HuggingDispatcher(name)
        elif name in ["openai"]:
            self.openai = agent_data.open_ai
        elif name in ["browse"]:
            self.browser = agent_data.browser
        elif name in ["scrape"]:
            self.scraper = "foo"
        else:
            raise ValueError(f"Invalid dispatcher name: {name}")
    
    def dispatch(self, *params):
        if self.api_dispatcher:
            r = self.api_dispatcher.make_api_call(*params)
            self.api_dispatcher = None
            return r
        elif self.hugging_dispatcher:
            return self.hugging_dispatcher.generate(params)
        elif self.openai:
            return self.openai.generate_text(*params, 0.3)
        elif self.browser:
            r = self.browser.scrape(params)
            self.browser = None
            return r
        elif self.scraper:
            r = ScrapperAgent(params).scrape()
            self.scraper = None
            return r
