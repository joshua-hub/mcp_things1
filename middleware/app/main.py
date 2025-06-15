"""MCP middleware implementation."""
import json
import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI
from config import config
import httpx
import re
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import os
from pathlib import Path

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
OLLAMA_API_URL = "http://ollama:11434"
MCP_SERVER_URL = "http://mcp-server:8000"

# Default system prompt fallback
DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant that can use tools. When you need to use a tool, wrap your request in <tool_request> tags with JSON format.

Available tools:
- get_current_time: Get current UTC time
- execute_python: Execute Python code in sandbox

Usage: <tool_request>{"name": "tool_name", "parameters": {...}}</tool_request>"""

def load_system_prompt() -> str:
    """Load system prompt from file with fallback to default."""
    try:
        prompt_file = Path("/app/system_prompt.md")
        if prompt_file.exists():
            return prompt_file.read_text(encoding="utf-8").strip()
        else:
            logger.warning("system_prompt.md not found, using default prompt")
            return DEFAULT_SYSTEM_PROMPT
    except Exception as e:
        logger.error(f"Error reading system_prompt.md: {e}, using default prompt")
        return DEFAULT_SYSTEM_PROMPT

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
            ollama_response = await client.get(f"{OLLAMA_API_URL}/api/version")
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
        logger.info(f"=== CHAT REQUEST START ===")
        logger.info(f"Received {len(request.messages)} messages")
        for i, msg in enumerate(request.messages):
            logger.info(f"Message {i}: {msg.role} - {msg.content[:100]}...")
        
        # Convert messages to OpenAI format
        messages = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        
        # Add system message if not present
        if not any(msg["role"] == "system" for msg in messages):
            system_prompt = load_system_prompt()
            logger.info(f"Adding system prompt (length: {len(system_prompt)})")
            logger.info(f"System prompt preview: {system_prompt[:500]}...")
            logger.info(f"System prompt contains tool examples: {'<tool_request>' in system_prompt}")
            logger.info(f"Full system prompt:\n{system_prompt}")
            messages.insert(0, {
                "role": "system",
                "content": system_prompt
            })
        else:
            logger.info("System message already present")

        logger.info(f"Sending {len(messages)} messages to LLM (model: {config.model_name})")
        
        # Get response from LLM
        response = client.chat.completions.create(
            model=config.model_name,
            messages=messages
        )
        
        # Extract the response content
        response_content = response.choices[0].message.content
        logger.info(f"LLM Response received (length: {len(response_content)})")
        logger.info(f"LLM Response content: {response_content}")

        # Check for tool request
        if "<tool_request>" in response_content:
            logger.info("🔧 Tool request detected in LLM response!")
            # Extract tool request
            tool_request = response_content.split("<tool_request>")[1].split("</tool_request>")[0]
            logger.info(f"Extracted tool request: {tool_request}")
            
            # Call MCP server
            try:
                tool_request_data = json.loads(tool_request)
                tool_name = tool_request_data["name"]
                tool_parameters = tool_request_data.get("parameters", {})
                
                logger.info(f"Calling MCP server at {MCP_SERVER_URL}/mcp/tools/{tool_name}")
                async with httpx.AsyncClient() as http_client:
                    mcp_response = await http_client.post(
                        f"{MCP_SERVER_URL}/mcp/tools/{tool_name}",
                        json=tool_parameters
                    )
                    if mcp_response.status_code != 200:
                        tool_response = {"error": f"MCP server error: {mcp_response.text}"}
                    else:
                        tool_response = mcp_response.json()
                    logger.info(f"MCP server response: {tool_response}")
            except json.JSONDecodeError as e:
                tool_response = {"error": f"Invalid tool request JSON: {e}"}
                logger.error(f"Failed to parse tool request: {tool_request}")

            # Send follow-up to LLM with tool response
            messages.append({"role": "assistant", "content": response_content})
            messages.append({
                "role": "user",
                "content": f"Tool response: {json.dumps(tool_response)}\n\nOriginal question: {request.messages[-1].content}"
            })
            
            logger.info("Sending follow-up request to LLM with tool response")
            response = client.chat.completions.create(
                model=config.model_name,
                messages=messages
            )
            response_content = response.choices[0].message.content
            logger.info(f"Final LLM response: {response_content}")
        else:
            logger.info("❌ No tool request found in LLM response")
            logger.info("LLM response did not contain <tool_request> tags")

        logger.info(f"=== CHAT REQUEST END ===")
        return ChatResponse(response=response_content)

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
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