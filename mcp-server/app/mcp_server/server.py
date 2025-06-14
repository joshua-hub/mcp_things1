"""MCP server implementation using FastAPI-MCP."""
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
from datetime import datetime
import logging
import prometheus_client
from prometheus_client import Counter, Histogram
import httpx
from .config import config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Setup metrics
tool_execution_time = Histogram(
    'mcp_tool_execution_seconds',
    'Time spent executing MCP tools',
    ['tool_name']
)
tool_execution_count = Counter(
    'mcp_tool_executions_total',
    'Total number of MCP tool executions',
    ['tool_name', 'status']
)

# Initialize FastAPI app
app = FastAPI(title="MCP Server")

# Initialize FastAPI-MCP
mcp = FastApiMCP(app)

@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "last_check": datetime.now().isoformat()
    }

@app.get("/ready")
async def readiness_check():
    """Readiness probe endpoint."""
    return {
        "status": "ready",
        "last_check": datetime.now().isoformat()
    }

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    from fastapi import Response
    return Response(
        content=prometheus_client.generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )

# Mount the MCP server
mcp.mount()
