import os
from typing import Dict, Any

# Default model configurations
DEFAULT_MODELS = {
    "completion": "gpt-4-turbo",
    "embedding": "text-embedding-ada-002",
    "mini": "gpt-4o-mini",
    "chat": "gpt-3.5-turbo"
}

def get_model_config() -> Dict[str, str]:
    """
    Get model configurations from environment variables with fallback to defaults.
    
    Environment variables:
    - BABYAGI_COMPLETION_MODEL: Model for completion tasks
    - BABYAGI_EMBEDDING_MODEL: Model for embedding tasks
    - BABYAGI_MINI_MODEL: Model for lightweight tasks
    - BABYAGI_CHAT_MODEL: Model for chat tasks
    
    Returns:
        Dict[str, str]: Dictionary containing model configurations
    """
    return {
        "completion": os.getenv("BABYAGI_COMPLETION_MODEL", DEFAULT_MODELS["completion"]),
        "embedding": os.getenv("BABYAGI_EMBEDDING_MODEL", DEFAULT_MODELS["embedding"]),
        "mini": os.getenv("BABYAGI_MINI_MODEL", DEFAULT_MODELS["mini"]),
        "chat": os.getenv("BABYAGI_CHAT_MODEL", DEFAULT_MODELS["chat"])
    }

# Get the current model configuration
MODEL_CONFIG = get_model_config() 