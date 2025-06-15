"""MCP server implementation - central aggregator for multiple MCP services."""
from fastapi import FastAPI, HTTPException
from fastapi_mcp import FastApiMCP
from datetime import datetime
import logging
import prometheus_client
from prometheus_client import Counter, Histogram
import httpx
from typing import Dict, List, Any
import asyncio
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
app = FastAPI(title="MCP Server - Central Aggregator")

# Initialize FastAPI-MCP
mcp = FastApiMCP(app)

# Service registry - map of service_name -> service_url
SERVICES = {
    "time-client": "http://time-client:8003",
    "code-executor": "http://code-executor:8002"
}

# Tool registry - map of tool_name -> service_name
tool_registry = {}

# Available tools cache
available_tools_cache = {}

async def discover_service_tools(service_name: str, service_url: str) -> List[str]:
    """Discover available tools from a service."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Try different possible endpoints to get tools
            endpoints_to_try = [
                f"{service_url}/tools",
                f"{service_url}/mcp/tools", 
                f"{service_url}/api/tools"
            ]
            
            for endpoint in endpoints_to_try:
                try:
                    response = await client.get(endpoint)
                    if response.status_code == 200:
                        tools = response.json()
                        if isinstance(tools, list):
                            logger.info(f"Discovered {len(tools)} tools from {service_name}: {tools}")
                            return tools
                        elif isinstance(tools, dict) and 'tools' in tools:
                            tool_list = tools['tools']
                            logger.info(f"Discovered {len(tool_list)} tools from {service_name}: {tool_list}")
                            return tool_list
                except Exception as e:
                    logger.debug(f"Failed to get tools from {endpoint}: {e}")
                    continue
            
            # If no tools endpoint found, try to infer from FastAPI-MCP endpoints
            # For time-client, we know it has get_current_time
            # For code-executor, we know it has execute_python
            if "time-client" in service_name:
                logger.info(f"Using known tools for {service_name}: ['get_current_time']")
                return ["get_current_time"]
            elif "code-executor" in service_name:
                logger.info(f"Using known tools for {service_name}: ['execute_python']")
                return ["execute_python"]
            
            logger.warning(f"No tools discovered for {service_name}")
            return []
            
    except Exception as e:
        logger.error(f"Failed to discover tools from {service_name} at {service_url}: {e}")
        return []

async def refresh_tool_registry():
    """Refresh the tool registry by discovering tools from all services."""
    global tool_registry, available_tools_cache
    
    tool_registry.clear()
    available_tools_cache.clear()
    
    for service_name, service_url in SERVICES.items():
        try:
            # Check if service is healthy first
            async with httpx.AsyncClient(timeout=5.0) as client:
                health_response = await client.get(f"{service_url}/health")
                if health_response.status_code != 200:
                    logger.warning(f"Service {service_name} is not healthy")
                    continue
            
            # Discover tools from this service
            tools = await discover_service_tools(service_name, service_url)
            
            # Register tools
            for tool in tools:
                tool_registry[tool] = service_name
                available_tools_cache[tool] = {
                    "name": tool,
                    "service": service_name,
                    "url": service_url
                }
                
        except Exception as e:
            logger.error(f"Failed to refresh tools for {service_name}: {e}")
    
    logger.info(f"Tool registry updated: {tool_registry}")

@app.on_event("startup")
async def startup_event():
    """Initialize tool discovery on startup."""
    await refresh_tool_registry()

@app.get("/mcp/tools")
async def get_available_tools():
    """Get list of all available tools from all services."""
    if not available_tools_cache:
        await refresh_tool_registry()
    
    return list(tool_registry.keys())

@app.post("/mcp/tools/{tool_name}")
async def execute_tool(tool_name: str, parameters: Dict[str, Any] = None):
    """Execute a tool by proxying to the appropriate service."""
    if tool_name not in tool_registry:
        await refresh_tool_registry()  # Try refreshing in case tools were added
        
    if tool_name not in tool_registry:
        raise HTTPException(
            status_code=404, 
            detail=f"Tool '{tool_name}' not found. Available tools: {list(tool_registry.keys())}"
        )
    
    service_name = tool_registry[tool_name]
    service_url = SERVICES[service_name]
    
    try:
        with tool_execution_time.labels(tool_name=tool_name).time():
            async with httpx.AsyncClient(timeout=30.0) as client:
                
                # Handle tool-specific endpoint patterns
                if tool_name == "get_current_time":
                    # Time client uses GET /current-time
                    try:
                        response = await client.get(f"{service_url}/current-time")
                        if response.status_code == 200:
                            tool_execution_count.labels(tool_name=tool_name, status="success").inc()
                            result = response.text.strip('"')  # Remove quotes from JSON string response
                            logger.info(f"Successfully executed {tool_name} via GET {service_url}/current-time")
                            return {"success": True, "output": result}
                        else:
                            logger.error(f"GET {service_url}/current-time failed: {response.status_code} - {response.text}")
                    except Exception as e:
                        logger.error(f"Failed to execute {tool_name} via GET: {e}")
                
                # For other tools, try standard POST endpoints
                endpoints_to_try = [
                    f"{service_url}/mcp/tools/{tool_name}",
                    f"{service_url}/tools/{tool_name}",
                    f"{service_url}/{tool_name}",
                    f"{service_url}/execute"  # For services that use generic execute endpoint
                ]
                
                for endpoint in endpoints_to_try:
                    try:
                        if parameters:
                            response = await client.post(endpoint, json=parameters)
                        else:
                            response = await client.post(endpoint, json={})
                            
                        if response.status_code == 200:
                            tool_execution_count.labels(tool_name=tool_name, status="success").inc()
                            result = response.json()
                            logger.info(f"Successfully executed {tool_name} via {endpoint}")
                            return result
                        elif response.status_code == 404:
                            continue  # Try next endpoint
                        else:
                            logger.error(f"Tool execution failed at {endpoint}: {response.status_code} - {response.text}")
                            
                    except Exception as e:
                        logger.debug(f"Failed to execute {tool_name} at {endpoint}: {e}")
                        continue
                
                # If all endpoints failed
                tool_execution_count.labels(tool_name=tool_name, status="error").inc()
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to execute {tool_name} on {service_name} - no working endpoints found"
                )
                
    except HTTPException:
        raise
    except Exception as e:
        tool_execution_count.labels(tool_name=tool_name, status="error").inc()
        logger.error(f"Error executing tool {tool_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")

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
