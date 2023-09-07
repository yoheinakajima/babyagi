import openai
import logging
from skills.skill import Skill
import os

# A little sloppy and experimental, but it's fun. Here's a demo: https://twitter.com/yoheinakajima/status/1699689836746358866

class PrettyMe(Skill):
    name = 'pretty_me'
    description = "A tool to update the current website UI by generating JavaScript that will execute upon load to change the front-end interface of the website it's on. The code response will be directly wrapped in a window.onload function and executed on the front-end. Use for any requests related to updating the UI (background, theme, etc.)"
    api_keys_required = ['openai']

    def __init__(self, api_keys, main_loop_function):
        super().__init__(api_keys, main_loop_function)

    def execute(self, params, dependent_task_outputs, objective):
        try:
            if not self.valid:
                return "API keys not configured properly."

            # Read the contents of your CSS and HTML files
            css_path = os.path.join("public", "static", "style.css")
            html_path = os.path.join("templates", "index.html")

            with open(css_path, 'r') as css_file, open(html_path, 'r') as html_file:
                css_content = css_file.read()
                html_content = html_file.read()

            # Prepare the prompt with CSS and HTML content
            task_prompt = f"Generate JavaScript code to execute based on the following user input: {objective} {params}\nCSS Content: {css_content}\nHTML Content: {html_content}\nInstructions: only provide Javascript code that would go between the script tags, but do not provide the script tags.\n### Code:"
            example_input2 = "make me nature themed."

            example_output2 = '''
            // Remove body background image and adjust body background color
            document.body.style.backgroundImage = "none";
            document.body.style.backgroundColor = "#4CAF50"; // Green color
            
            // Adjust chat box background color
            document.querySelector(".chat-box").style.backgroundColor = "#4CAF50"; // Green color
            
            // Adjust chat messages' background color and bubble tail styles
            document.querySelectorAll(".bg-blue-200").forEach(function(element) {
                element.style.backgroundColor = "#357E68"; // Darker green
            });
            document.querySelectorAll(".bg-gray-300").forEach(function(element) {
                element.style.backgroundColor = "#295E4C"; // Darker green
                element.style.borderLeftColor = "#357E68"; // Border color matching user's bubble
            });
            
            // Adjust objectives box background color
            document.querySelector(".objectives-box").style.backgroundColor = "#4CAF50"; // Green color
            
            // Adjust task item background color
            document.querySelectorAll(".task-item").forEach(function(element) {
                element.style.backgroundColor = "#295E4C"; // Darker green
            });
            
            // Adjust task output background color
            document.querySelectorAll(".task-output").forEach(function(element) {
                element.style.backgroundColor = "#fffdfd"; // Light gray
            });
            '''

# Use the example2 variable in your execute function


            messages = [
                {"role": "user", "content": example_input2},
                {"role": "assistant", "content": example_output2},
                {"role": "user", "content": "make my background red."},
                {"role": "assistant", "content": "document.body.style.backgroundColor = \"red\";\ndocument.body.style.backgroundImage = \"none\";"},
                {"role": "user", "content": task_prompt}
            ]
            print(messages)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=messages,
                temperature=0,
                max_tokens=4000,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0
            )
            
            generated_code = response.choices[0].message['content'].strip()

            # Wrap the generated code with an onload event handler
            wrapped_code = f'''
            <script>
                var script = document.createElement("script");
                script.type = "text/javascript";
                script.innerHTML = `{generated_code}`;
                document.head.appendChild(script);
            </script>
            '''
            return "\n\n" + wrapped_code
        except Exception as exc:
            # Log the exception for debugging
            logging.error(f"Error in PrettyMe skill: {exc}")
            # Return a user-friendly error message
            return "An error occurred while processing your request."
