from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from typing import Dict, Any, List, Type

from mcp.server import Server
from mcp.types import ToolResult

from .tools.code_execution import CodeExecutionTool
from .tools.time import TimeTool

class MCPServer:
    """Main MCP server that manages multiple tools.
    
    This server provides a unified interface for multiple MCP tools,
    allowing them to be enabled/disabled via configuration.
    """
    
    def __init__(self, enabled_tools: List[str] = None):
        """Initialize the MCP server.
        
        Args:
            enabled_tools: List of tool names to enable. If None, all tools are enabled.
        """
        self.server = Server("mcp-server")
        self.tools = {}
        self.enabled_tools = enabled_tools or ["code_execution", "time"]
        self._initialize_tools()
        self._register_tools()
    
    def _initialize_tools(self):
        """Initialize enabled tools."""
        if "code_execution" in self.enabled_tools:
            self.tools["code_execution"] = CodeExecutionTool()
        if "time" in self.enabled_tools:
            self.tools["time"] = TimeTool()
    
    def _register_tools(self):
        """Register enabled tools with the server."""
        if "code_execution" in self.tools:
            self.server.register_tool(
                "execute_code",
                self.tools["code_execution"].execute_code,
                "Execute Python code in a sandboxed environment. This tool allows you to run Python code safely, with access to the Python standard library and numpy. It is part of the MCP server's capabilities."
            )
        
        if "time" in self.tools:
            self.server.register_tool(
                "get_current_time",
                self.tools["time"].get_current_time,
                "Get the current time in UTC ISO format. This tool provides the current time in a standardized format, allowing you to derive date and/or time as needed. It is part of the MCP server's capabilities."
            )
    
    @asynccontextmanager
    async def lifespan(self) -> AsyncIterator[Dict[str, Any]]:
        """Manage server lifecycle and tool cleanup."""
        try:
            yield {}
        finally:
            # Clean up tools
            for tool in self.tools.values():
                if hasattr(tool, "cleanup"):
                    tool.cleanup()
    
    def get_server(self) -> Server:
        """Get the configured MCP server instance."""
        return self.server
