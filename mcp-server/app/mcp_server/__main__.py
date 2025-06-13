import asyncio
import uvicorn
import os
from typing import List

from .server import MCPServer

def main():
    """Main entry point for running the MCP server."""
    # Get enabled tools from environment variable
    enabled_tools = os.getenv("MCP_ENABLED_TOOLS", "").split(",")
    enabled_tools = [t.strip() for t in enabled_tools if t.strip()]
    
    # Create and run server
    server = MCPServer(enabled_tools=enabled_tools if enabled_tools else None)
    app = server.get_server().app
    app.lifespan = server.lifespan
    
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    asyncio.run(server.serve())

if __name__ == "__main__":
    main()
