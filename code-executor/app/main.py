"""Code execution MCP client that forwards to sandbox."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi_mcp import FastApiMCP
import httpx
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Code Execution MCP Client")

SANDBOX_URL = "http://sandbox:8001"

class CodeRequest(BaseModel):
    code: str

@app.post("/execute-code", operation_id="execute_code", summary="Execute Python code in sandbox")
async def execute_code(request: CodeRequest) -> dict:
    """
    Forward code execution request to sandbox container.
    
    Args:
        request: CodeRequest containing the Python code to execute
        
    Returns:
        Dict containing execution results or error information
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SANDBOX_URL}/execute",
                json={"code": request.code}
            )
            response.raise_for_status()
            return response.json()
            
    except Exception as e:
        logger.error(f"Error forwarding code execution: {str(e)}")
        return {
            "status": "error",
            "error": str(e)
        }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

# Initialize FastAPI-MCP and mount it
mcp = FastApiMCP(app)
mcp.mount()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002) 