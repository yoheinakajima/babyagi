import sys

def user_input_await(prompt: str) -> str:
    print("\033[94m\033[1m" + "\n> COPY FOLLOWING TEXT TO CHATBOT\n" + "\033[0m\033[0m")
    print(prompt)
    print("\033[91m\033[1m" + "\n AFTER PASTING, PRESS: (ENTER), (CTRL+Z), (ENTER) TO FINISH\n" + "\033[0m\033[0m")
    print("\033[96m\033[1m" + "\n> PASTE YOUR RESPONSE:\n" + "\033[0m\033[0m")
    input_text = sys.stdin.read()
    return input_text.strip()