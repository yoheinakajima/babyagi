import os
from apis.api_factory import ArxivAPI, ClinicalTrialsAPI, JSONPlaceholderAPI, NHANESApi, NewsApi, OpenWeatherAPI, PubMedAPI, WikipediaAPI, YelpFusionAPI

class APIDispatcher:
    def __init__(self, api_name):
        self.api_name = api_name
        self.api = self.get_api()
        
    def get_api(self):
        if self.api_name == "yelp":
            YELP_API_KEY = os.getenv("YELP_API_KEY", "")
            return YelpFusionAPI(YELP_API_KEY)
        elif self.api_name == "arxiv":
            return ArxivAPI()
        elif self.api_name == "wikipedia":
            return WikipediaAPI()
        elif self.api_name == "openweather":
            OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
            return OpenWeatherAPI(OPENWEATHER_API_KEY)
        elif self.api_name == "jsonplaceholder":
            return JSONPlaceholderAPI("foo")
        elif self.api_name == "nhanes":
            return NHANESApi()
        elif self.api_name == "newsapi":
            NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
            return NewsApi(NEWS_API_KEY)
        elif self.api_name == "pubmed":
            PUBMED_API_MAIL = os.getenv("PUBMED_API_MAIL", "")
            return PubMedAPI(PUBMED_API_MAIL)
        elif self.api_name == "clinicaltrials":
            return ClinicalTrialsAPI()
        else:
            raise ValueError("Invalid API name.")
        
    def make_api_call(self, *args):
        return self.api.make_api_call(*args)
