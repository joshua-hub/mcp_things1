"""MCP middleware implementation."""
import json
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from .config import config
import httpx
import re
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="MCP Middleware")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
client = OpenAI(
    base_url=config.base_url,
    api_key=config.api_key
)

# Configuration
OLLAMA_API_URL = "http://host.docker.internal:11434"
MCP_SERVER_URL = "http://mcp-server:8000"

# Service health status
health_state = {
    "mcp_server": {"status": "unknown", "last_check": None},
    "ollama": {"status": "unknown", "last_check": None}
}

class Message(BaseModel):
    """Message model for chat."""
    content: str
    role: str = "user"

class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[Message]

class ChatResponse(BaseModel):
    """Chat response model."""
    response: str

class ToolRequest(BaseModel):
    name: str
    parameters: Dict[str, Any]

class ServiceHealth(BaseModel):
    status: str
    last_check: Optional[datetime]

async def check_service_health() -> Dict[str, ServiceHealth]:
    """Check health of all services."""
    async with httpx.AsyncClient() as client:
        # Check MCP Server
        try:
            response = await client.get(f"{MCP_SERVER_URL}/health")
            health_state["mcp_server"] = {
                "status": "healthy" if response.status_code == 200 else "unhealthy",
                "last_check": datetime.now()
            }
        except Exception as e:
            health_state["mcp_server"] = {
                "status": "unhealthy",
                "last_check": datetime.now()
            }

        # Check Ollama
        try:
            ollama_response = await client.get(f"{OLLAMA_API_URL}/api/health")
            health_state["ollama"] = {
                "status": "healthy" if ollama_response.status_code == 200 else "unhealthy",
                "last_check": datetime.now()
            }
        except Exception as e:
            health_state["ollama"] = {
                "status": "unhealthy",
                "last_check": datetime.now()
            }

    return health_state

async def get_available_tools() -> List[str]:
    """Get list of available tools from MCP server."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{MCP_SERVER_URL}/mcp/tools")
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to get tools from MCP server")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tools: {str(e)}")

async def extract_tool_request(text: str) -> Optional[ToolRequest]:
    """Extract tool request from Llama's response."""
    pattern = r"<tool_request>(.*?)</tool_request>"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        try:
            return ToolRequest(**json.loads(match.group(1)))
        except json.JSONDecodeError:
            return None
    return None

async def call_mcp_tool(tool_request: ToolRequest) -> Dict[str, Any]:
    """Call the MCP server with the tool request."""
    # Verify tool exists
    available_tools = await get_available_tools()
    if tool_request.name not in available_tools:
        raise HTTPException(
            status_code=400,
            detail=f"Tool '{tool_request.name}' is not available. Available tools: {available_tools}"
        )

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{MCP_SERVER_URL}/mcp/tools/{tool_request.name}",
                json=tool_request.parameters
            )
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Tool execution failed: {response.text}")
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """Handle chat requests."""
    try:
        # Convert messages to OpenAI format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Add system message if not present
        if not any(msg["role"] == "system" for msg in messages):
            messages.insert(0, {
                "role": "system",
                "content": "You are a helpful assistant that can use tools. When you need to use a tool, wrap your request in <tool_request> tags."
            })

        # Get response from LLM
        response = client.chat.completions.create(
            model=config.model_name,
            messages=messages
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content

        # Check for tool request
        if "<tool_request>" in response_content:
            # Extract tool request
            tool_request = response_content.split("<tool_request>")[1].split("</tool_request>")[0]
            
            # Call MCP server
            async with httpx.AsyncClient() as client:
                mcp_response = await client.post(
                    f"{MCP_SERVER_URL}/execute",
                    json={"request": tool_request}
                )
                tool_response = mcp_response.json()

            # Send follow-up to LLM with tool response
            messages.append({"role": "assistant", "content": response_content})
            messages.append({
                "role": "user",
                "content": f"Tool response: {json.dumps(tool_response)}\n\nOriginal question: {request.messages[-1].content}"
            })

            response = client.chat.completions.create(
                model=config.model_name,
                messages=messages
            )
            response_content = response.choices[0].message.content

        return ChatResponse(response=response_content)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    health = await check_service_health()
    return {
        "status": "healthy" if all(s["status"] == "healthy" for s in health.values()) else "unhealthy",
        "services": health
    }

@app.get("/tools")
async def get_tools():
    """List available tools from MCP server."""
    return await get_available_tools()

@app.post("/execute")
async def execute_tool(tool_request: ToolRequest):
    """Execute a tool via MCP server."""
    return await call_mcp_tool(tool_request) 