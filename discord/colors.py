class Colors:
    BLACK = "\033[90m\033[1m"
    RED = "\033[91m\033[1m"
    GREEN = "\033[92m\033[1m"
    YELLOW = "\033[93m\033[1m"
    BLUE = "\033[94m\033[1m"
    MAGENTA = "\033[95m\033[1m"
    CYAN = "\033[96m\033[1m"
    WHITE = "\033[97m\033[1m"
    NEUTRAL = "\033[0m\033[0m"

def colorize(text, color):
    return color + text + Colors.NEUTRAL
