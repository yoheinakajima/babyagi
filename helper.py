import os
import sys
import openai

def openai_call(prompt: str, use_gpt4: bool = False, temperature: float = 0.5, max_tokens: int = 100):
    if not use_gpt4:
        #Call GPT-3 DaVinci model
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].text.strip()
    else:
        #Call GPT-4 chat model
        messages=[{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages = messages,
            temperature=temperature,
            max_tokens=max_tokens,
            n=1,
            stop=None,
        )
        return response.choices[0].message.content.strip()

def save_script_to_file(code: str, filename: str, folder: str = "generated_scripts"):
    # Create the folder if it doesn't exist
    if not os.path.exists(folder):
        os.makedirs(folder)

    # Save the code to a file
    with open(os.path.join(folder, filename), "w") as file:
        file.write(code)

def execute_terminal_command(command: str):
    # Clean the command by removing any newlines
    command = command.replace("\n", "")
    # Execute the command
    os.system(command)