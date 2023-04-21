from .singleton import Singleton
from dotenv import load_dotenv
import os
load_dotenv()


class Config(metaclass=Singleton):
    def __init__(self):
        # OpenAI API Keys
        self.open_ai_key = os.getenv("OPENAI_API_KEY", "")
        assert self.open_ai_key, "\033[91m\033[1m" + \
            "OPENAI_API_KEY environment variable is missing from .env" + \
            "\033[0m\033[0m"
        # Table config
        self.restuls_store_name = os.getenv(
            "RESULTS_STORE_NAME", os.getenv("TABLE_NAME", ""))
        assert self.restuls_store_name, "\033[91m\033[1m" + \
            "RESULTS_STORE_NAME environment variable is missing from .env" + \
            "\033[0m\033[0m"
        # Run configuration
        self.instance_name = os.getenv(
            "INSTANCE_NAME", os.getenv("BABY_NAME", "BabyAGI"))
        self.cooperative_mode = "none"
        self.join_existing_objective = False
        # Goal configuation
        self.objective = os.getenv("OBJECTIVE", "")
        assert self.objective, "\033[91m\033[1m" + \
            "OBJECTIVE environment variable is missing from .env" + \
            "\033[0m\033[0m"
        self.initial_task = os.getenv(
            "INITIAL_TASK", os.getenv("FIRST_TASK", ""))
        assert self.initial_task, "\033[91m\033[1m" + \
            "INITIAL_TASK environment variable is missing from .env" + \
            "\033[0m\033[0m"
        # Pinecone configuration
        self.pinecone_api_key = os.getenv("PINECONE_API_KEY", "")
        self.pinecone_environment = os.getenv("PINECONE_ENVIRONMENT", "")
        self.pinecone_table_name = os.getenv("TABLE_NAME", "")
        # Model configuration
        self.openai_temperature = float(os.getenv("OPENAI_TEMPERATURE", 0.0))
        self.llm_model = os.getenv("LLM_MODEL", os.getenv(
            "OPENAI_API_MODEL", "gpt-3.5-turbo"))
        self.llama_model_path = os.getenv(
            "LLAMA_MODEL_PATH", "models/llama-13B/ggml-model.bin")
        # Extensions
        self.dotenv_extensions = os.getenv("DOTENV_EXTENSIONS", "").split(" ")
        # Command line arguments extension
        # Can override any of the above environment variables
        self.enable_command_line_args = (
            os.getenv("ENABLE_COMMAND_LINE_ARGS", "false").lower() == "true"
        )
