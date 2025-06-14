from pydantic_settings import BaseSettings
from pydantic import Field
import os

class LLMConfig(BaseSettings):
    """LLM configuration settings."""
    base_url: str = Field(default="http://localhost:11434/v1")
    api_key: str = Field(default="ollama")
    model_name: str = Field(default="llama2")

    class Config:
        env_prefix = "LLM_"
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create config instance
config = LLMConfig() 