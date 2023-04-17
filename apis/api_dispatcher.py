from apis.api_factory import ArxivAPI, ClinicalTrialsAPI, JSONPlaceholderAPI, NHANESApi, NewsApi, OpenWeatherAPI, PubMedAPI, WikipediaAPI, YelpFusionAPI

class APIDispatcher:
    def __init__(self, api_name):
        self.api_name = api_name
        self.api = self.get_api()
        
    def get_api(self):
        if self.api_name == "yelp":
            return YelpFusionAPI()
        elif self.api_name == "arxiv":
            return ArxivAPI()
        elif self.api_name == "wikipedia":
            return WikipediaAPI()
        elif self.api_name == "openweather":
            return OpenWeatherAPI()
        elif self.api_name == "jsonplaceholder":
            return JSONPlaceholderAPI("foo")
        elif self.api_name == "nhanes":
            return NHANESApi()
        elif self.api_name == "newsapi":
            return NewsApi()
        elif self.api_name == "pubmed":
            return PubMedAPI()
        elif self.api_name == "clinicaltrials":
            return ClinicalTrialsAPI()
        else:
            raise ValueError("Invalid API name.")
        
    def make_api_call(self, *args):
        return self.api.make_api_call(*args)
