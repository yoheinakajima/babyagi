def is_valid_python_script(code: str) -> bool:
    return "--PYTHON SCRIPT--" in code

def is_valid_javascript_script(code: str) -> bool:
    return "--JAVASCRIPT SCRIPT--" in code

def is_valid_css_script(code: str) -> bool:
    return "--CSS SCRIPT--" in code

def is_valid_terminal_command(code: str) -> bool:
    return "--TERMINAL COMMAND--" in code
