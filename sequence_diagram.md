# System Architecture Documentation

## Overview

This MCP (Model Control Protocol) system consists of 5 microservices orchestrated via Docker Compose:

- **mcp-server** (port 8000): Main MCP server providing system coordination
- **middleware** (port 8002): Request processing and routing middleware  
- **sandbox** (port 8001): Pure code execution environment (FastAPI REST)
- **code-executor** (port 8004): MCP server providing code execution tools (delegates to sandbox)
- **time-client** (port 8003): MCP server providing time-related tools

Additional monitoring services:
- **Prometheus** (port 9090): Metrics collection
- **Grafana** (port 3000): Metrics visualization

## MCP Tools Available

### Time Tools (via time-client:8003)
- `get_current_time`: Returns current UTC time in ISO format
- `get_timezone_time`: Get time in specific timezone
- `format_time`: Format time strings

### Code Execution Tools (via code-executor:8004)
- `execute_python`: Execute Python code in sandboxed environment
- `install_package`: Install Python packages in sandbox
- `list_packages`: List installed packages

### System Tools (via mcp-server:8000)
- `get_system_status`: Get overall system health
- `get_service_metrics`: Get service performance metrics

## Architecture Flow

```mermaid
graph TB
    subgraph "External"
        User[User/Client]
        Prometheus[Prometheus:9090]
        Grafana[Grafana:3000]
    end
    
    subgraph "MCP Services"
        MCP[mcp-server:8000<br/>Main MCP Server]
        MW[middleware:8002<br/>Request Middleware]
        CE[code-executor:8004<br/>MCP Code Tools]
        TC[time-client:8003<br/>MCP Time Tools]
    end
    
    subgraph "Execution Environment"
        SB[sandbox:8001<br/>Pure Execution<br/>FastAPI REST]
    end
    
    User --> MCP
    MCP --> MW
    MW --> CE
    MW --> TC
    CE --> SB
    
    Prometheus --> MCP
    Prometheus --> MW  
    Prometheus --> CE
    Prometheus --> TC
    Prometheus --> SB
    
    Grafana --> Prometheus
```

## Sequence Diagram: Time Query

```mermaid
sequenceDiagram
    participant User
    participant MW as middleware:8002
    participant TC as time-client:8003

    User->>MW: MCP Request: get_current_time
    MW->>TC: HTTP POST /mcp/tools/get_current_time
    TC->>TC: Process time request
    TC->>MW: Return time data
    MW->>User: MCP Response: "2024-01-15T14:30:00+00:00 UTC"
```

## Sequence Diagram: Code Execution

```mermaid
sequenceDiagram
    participant User
    participant MW as middleware:8002
    participant CE as code-executor:8004
    participant SB as sandbox:8001

    User->>MW: MCP Request: execute_python
    MW->>CE: HTTP POST /mcp/tools/execute_python
    CE->>SB: HTTP POST /execute {"code": "print('hello')"}
    SB->>SB: Execute Python code safely
    SB->>CE: Return execution result
    CE->>MW: Return MCP tool response
    MW->>User: MCP Response: execution output
```

## Service Communication

### MCP Protocol
- Standard MCP over HTTP between MCP-enabled services
- JSON-RPC 2.0 format for tool calls
- Automatic tool discovery and registration

### REST API (Internal)
- Sandbox uses pure FastAPI REST endpoints
- code-executor translates MCP calls to REST calls
- Prometheus metrics endpoints on all services

### Service Discovery
Services communicate via Docker Compose networking:
- `mcp-server:8000` - Main MCP endpoint
- `middleware:8002` - Request processing  
- `sandbox:8001` - Code execution
- `code-executor:8004` - MCP wrapper for sandbox
- `time-client:8003` - Time services

## Error Handling

### Code Execution Errors
- Syntax errors returned with traceback  
- Runtime exceptions captured safely
- Timeout protection (30s default)
- Memory limits enforced

### Service Failures
- Health checks on all services
- Graceful degradation when services unavailable
- Retry logic with exponential backoff
- Circuit breaker patterns

## Monitoring

### Metrics Collection
- Prometheus scrapes `/metrics` endpoints
- Custom metrics for tool usage, latency, errors
- System resource monitoring

### Visualization  
- Grafana dashboards for service health
- Real-time performance monitoring
- Error rate tracking and alerting

## Usage Examples

### Direct MCP Client
```python
import httpx

# Call time tool
response = httpx.post("http://localhost:8000/mcp/tools/get_current_time", 
                     json={"params": {}})

# Call code execution  
response = httpx.post("http://localhost:8000/mcp/tools/execute_python",
                     json={"params": {"code": "print('Hello, World!')"}})
```

### Health Checks
```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:8002/health  
curl http://localhost:8001/health
curl http://localhost:8004/health
curl http://localhost:8003/health

# View metrics
curl http://localhost:8000/metrics
``` 