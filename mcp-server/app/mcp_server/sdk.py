"""
Simplified MCP SDK implementation.
"""
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: Optional[str] = None
    error: Optional[str] = None

class Server:
    """MCP Server implementation."""
    
    def __init__(self, name: str):
        """Initialize the server.
        
        Args:
            name: Name of the server.
        """
        self.name = name
        self.app = FastAPI(title=name)
        self.tools: Dict[str, Dict[str, Any]] = {}
        
        # Add health check endpoint
        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}
        
        # Add tools endpoint
        @self.app.get("/tools")
        async def list_tools():
            return list(self.tools.keys())
    
    def register_tool(self, name: str, handler: Callable, description: str):
        """Register a tool with the server.
        
        Args:
            name: Name of the tool.
            handler: Function that handles the tool request.
            description: Description of the tool.
        """
        self.tools[name] = {
            "handler": handler,
            "description": description
        }
        
        # Add tool endpoint
        @self.app.post(f"/tools/{name}")
        async def tool_endpoint(request: Dict[str, Any]):
            try:
                result = await handler(**request)
                if isinstance(result, ToolResult):
                    return {
                        "success": result.success,
                        "output": result.output,
                        "error": result.error
                    }
                return {"success": True, "output": str(result)}
            except Exception as e:
                return {
                    "success": False,
                    "error": str(e)
                }
    
    def get_app(self) -> FastAPI:
        """Get the FastAPI application."""
        return self.app 