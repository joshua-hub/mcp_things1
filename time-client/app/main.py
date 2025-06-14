"""Time tool implementation."""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from datetime import datetime, timezone
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Time Tool")

@app.get("/current-time", operation_id="get_current_time", summary="Get the current time in UTC ISO format")
async def get_current_time() -> str:
    """Get the current time in UTC ISO format.
    
    Returns:
        Current time in UTC ISO format
    """
    current_time = datetime.now(timezone.utc).isoformat() + " UTC"
    logger.info(f"Time tool returning: {current_time}")
    return current_time

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Initialize FastAPI-MCP and mount it
mcp = FastApiMCP(app)
mcp.mount() 