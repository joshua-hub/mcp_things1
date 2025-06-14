"""MCP server configuration."""
from pydantic_settings import BaseSettings

class Config(BaseSettings):
    """MCP server configuration."""
    time_client_url: str = "http://time-client:8001"
    code_executor_url: str = "http://code-executor:8002"

    class Config:
        env_prefix = "MCP_"
        env_file = ".env"
        env_file_encoding = "utf-8"

# Create config instance
config = Config() 