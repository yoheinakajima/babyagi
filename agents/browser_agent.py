from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from duckduckgo_search import ddg
from agents.scrapper_agent import ScrapperAgent

class BrowserAgent:
    def __init__(self, api_key, engine_id):
        self.api_key = api_key
        self.service = build('customsearch', 'v1', developerKey=api_key)
        self.fallback_service = ddg
        self.engine_id = engine_id
        

    def browse(self, query, num_results=3):
        try:
            
            if isinstance(query, str):
                strip_query = query.replace('\\', ' ')
       
            elif isinstance(query, tuple):
        
                old_value, *rest = query
                strip_query = old_value.replace('\\', ' ')
            
            res = self.service.cse().list(q=strip_query, cx=self.engine_id, num=num_results).execute()

            links = [r['link'] for r in res['items']]
            return links[:2]
        
        except HttpError as error:
            print(f'An error occurred: {error}')
            if error.resp.status == 429:
                if isinstance(query, str):
                    strip_query = query.replace('\\', ' ')
       
                elif isinstance(query, tuple):
                    old_value, *rest = query
                    strip_query = old_value.replace('\\', ' ')
                
                data = self.fallback_service(strip_query)
                print(data)
                links = [r['href'] for r in data]
                print(links)
                return links[:2]
            else:
                return []
        
    def scrape(self, query):
        results = self.browse(query)
        
        scraped_data = []
        for result in results:
            link = result
            scrapper = ScrapperAgent(link)
            
            scraped_data.append(scrapper.scrape())
        
        return scraped_data