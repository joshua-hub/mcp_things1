from pydantic_settings import BaseSettings
from pydantic import Field
import os
import logging

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMConfig(BaseSettings):
    """LLM configuration settings."""
    base_url: str = Field(default="http://ollama:11434/v1")
    api_key: str = Field(default="ollama")
    model_name: str = Field(default="llama3.1:latest")

    class Config:
        env_prefix = "LLM_"
        env_file = "/app/.env"
        env_file_encoding = "utf-8"

# Create config instance
logger.info("Loading configuration...")
logger.info(f"Looking for .env file at: /app/.env")
logger.info(f"File exists: {os.path.exists('/app/.env')}")

config = LLMConfig()

logger.info(f"Loaded config - base_url: {config.base_url}")
logger.info(f"Loaded config - api_key: {'***' if config.api_key != 'ollama' else config.api_key}")
logger.info(f"Loaded config - model_name: {config.model_name}") 