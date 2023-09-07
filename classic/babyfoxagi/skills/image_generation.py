from skills.skill import Skill
import openai
import litellm
import requests
import os
from urllib.parse import urlparse

class ImageGeneration(Skill):
    name = 'image_generation'
    description = "A drawing tool that uses OpenAI's DALL-E API to generate images."
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
            {"role": "system", "content": "You are a helpful assistant specialized in generating creative and descriptive prompts for image generation. Your response is always one sentence with no line breaks. If the input is already detailed, do not change it."},
            {"role": "user", "content": "Generate a prompt for image creation based on the following objective: Draw a dystopian industrial city"},
            {"role": "assistant", "content": "Realistic painting of a dystopian industrial city with towering factories, pollution-filled air, and a gloomy sky."},
            {"role": "user", "content": "Generate a prompt for image creation based on the following objective: Draw interior photography of a cozy corner in a coffee shop, using natural light."},
            {"role": "assistant", "content": "Interior photography of a cozy corner in a coffee shop, using natural light."},
            {"role": "user", "content": "Generate a prompt for image creation based on the following objective: Draw an enchanted forest"},
            {"role": "assistant", "content": "Whimsical painting of an enchanted forest with mythical creatures, vibrant colors, and intricate details."},
            {"role": "user", "content": "Generate a prompt for image creation based on the following objective: " + objective}
        ]
        
        response = litellm.completion(
            model="gpt-3.5-turbo",
            messages=prompt_generation_messages
        )
        
        return response.choices[0].message['content'].strip()
    
    def execute(self, params, dependent_task_outputs, objective):
        if not self.valid:
            return
        print(f"Objective: {objective}")
    
        # Generate a creative prompt for DALL-E based on the objective
        generated_prompt = self.generate_prompt(objective)
        print(f"generated_prompt: {generated_prompt}")
    
        # Make API request to generate image based on the generated prompt
        response = openai.Image.create(
            prompt=generated_prompt,
            n=1,
            size="512x512",
            response_format="url"
        )
    
        # Extract URL of the generated image
        image_url = response.data[0]['url']
        print(f"image_url: {image_url}")
    
        # Download and save the image to your specified folder
        saved_image_path = self.download_and_save_image(image_url)
        print(f"saved_image_path: {saved_image_path}")

        # Generate the HTML code with a hard-coded relative path to display the image
        relative_image_path = os.path.relpath(saved_image_path, start="public")
        print(f"relative_image_path: {relative_image_path}")
        
        # The path is hardcoded here based on what you said works
        html_code = f'<img src="static/images/{os.path.basename(saved_image_path)}" alt="Generated Image">'
        print(f"html_code: {html_code}")

        return html_code
