from skills.skill import Skill
import openai
import requests
import os
import json
from urllib.parse import urlparse

class PlayMusic(Skill):
    name = 'play_music'
    description = "A skill that uses the Deezer API to search for music and play it with an html player."
    api_keys_required = ['openai']

    def __init__(self, api_keys, main_loop_function):
        super().__init__(api_keys, main_loop_function)
    
    def download_and_save_image(self, url, folder_path="public/static/images"):
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)
        
        response = requests.get(url)
        
        # Extract file name from URL
        parsed_url = urlparse(url)
        file_name = os.path.basename(parsed_url.path)
        
        # Save image to folder
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'wb') as f:
            f.write(response.content)
        
        return file_path

    def generate_prompt(self, objective):
        prompt_generation_messages = [
            {"role": "system", "content": "You are a helpful assistant specialized in generating a query for Deezer's music API which is a query and search type. Search types are artist, album name, genre, and track name. Both query and search type should have single quotes, and separated by a comma"},
            {"role": "user", "content": "Play some Eminem"},
            {"role": "assistant", "content": "'Eminem','artist'"},
            {"role": "user", "content": "Play tropical house."},
            {"role": "assistant", "content": "'tropical house','genre'"},
            {"role": "user", "content": "Play 99 problems"},
            {"role": "assistant", "content": "'99 problems','track'"},
            {"role": "user", "content": "Play abbey road"},
            {"role": "assistant", "content": "'abbey road','album'"},
            {"role": "user", "content": objective}
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=prompt_generation_messages
        )
        
        return response.choices[0].message['content'].strip()

  
    def deezer_search(self, query, search_type):
        base_url = "https://api.deezer.com/search"
        
        params = {"q": f"{search_type}:'{query}'"}
        
        response = requests.get(base_url, params=params)
        
        if response.status_code != 200:
            print("Failed to get data:", response.status_code)
            return None
        
        results = json.loads(response.text)
        
        if not results['data']:
            print("No results found")
            return None
        
        first_result = results['data'][0]
        
        if search_type == "artist":
            artist_id = first_result['artist']['id']
            return f'<iframe title="deezer-widget" src="https://widget.deezer.com/widget/dark/artist/{artist_id}/top_tracks" width="100%" height="300" frameborder="0" allowtransparency="true" allow="encrypted-media; clipboard-write"></iframe>'
        elif search_type == "album":
            album_id = first_result['album']['id']
            return f'<iframe title="deezer-widget" src="https://widget.deezer.com/widget/dark/album/{album_id}" width="100%" height="300" frameborder="0" allowtransparency="true" allow="encrypted-media; clipboard-write"></iframe>'
        elif search_type == "track":
            track_id = first_result['id']
            return f'<iframe title="deezer-widget" src="https://widget.deezer.com/widget/dark/track/{track_id}" width="100%" height="300" frameborder="0" allowtransparency="true" allow="encrypted-media; clipboard-write"></iframe>'
        elif search_type == "genre":
            genre_id = first_result['id']
            return f'<iframe title="deezer-widget" src="https://widget.deezer.com/widget/dark/genre/{genre_id}" width="100%" height="300" frameborder="0" allowtransparency="true" allow="encrypted-media; clipboard-write"></iframe>'
        else:
            print("Unsupported search type")
            return None
    
    def execute(self, params, dependent_task_outputs, objective):
        if not self.valid:
            return
        print(f"Objective: {objective}")

        generated_prompt = self.generate_prompt(objective)
        print(f"generated_prompt: {generated_prompt}")

        query, search_type = [x.strip().strip("'") for x in generated_prompt.split(",")]

        response = self.deezer_search(query, search_type)  # Modified this line

        return response
