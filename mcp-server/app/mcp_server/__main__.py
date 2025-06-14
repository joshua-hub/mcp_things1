"""MCP server entry point."""
import asyncio
import sys
import uvicorn
from .server import app, initialize_server

async def run_stdio_server():
    """Run the MCP server using stdio streams."""
    try:
        await initialize_server()
    except Exception as e:
        print(f"Failed to initialize MCP server: {e}", file=sys.stderr)
        sys.exit(1)

async def run_servers():
    """Run both stdio and FastAPI servers."""
    # Start the stdio server
    stdio_task = asyncio.create_task(run_stdio_server())
    
    # Start the FastAPI server
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()
    
    # Wait for stdio server
    await stdio_task

def main():
    """Main entry point."""
    asyncio.run(run_servers())

if __name__ == "__main__":
    main()
