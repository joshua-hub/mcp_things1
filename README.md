# MCP Distributed System

A distributed Model Context Protocol (MCP) implementation featuring secure code execution, middleware orchestration, and microservices architecture. This project demonstrates a production-ready MCP system with multiple specialized services working together.

## Architecture Overview

The system consists of five main services orchestrated via Docker Compose:

### 🚀 **MCP Server** (`mcp-server`)
- **Port**: 8000
- **Role**: Central MCP protocol handler and coordinator
- **Technology**: FastAPI with FastAPI-MCP integration
- **Features**: Health checks, metrics, tool registration

### 🔧 **Middleware** (`middleware`) 
- **Port**: 8002
- **Role**: Chat interface and LLM integration
- **Technology**: FastAPI with OpenAI/Ollama integration
- **Features**: Chat API, tool orchestration, service health monitoring

### 🛡️ **Sandbox** (`sandbox`)
- **Port**: 8001  
- **Role**: Secure Python code execution environment
- **Technology**: FastAPI-MCP with security controls
- **Features**: Code execution, package installation, security validation

### 💻 **Code Executor** (`code-executor`)
- **Port**: 8003
- **Role**: MCP client that forwards code execution to sandbox
- **Technology**: FastAPI-MCP client
- **Features**: Tool interface for code execution

### ⏰ **Time Client** (`time-client`)
- **Port**: 8003
- **Role**: Time-related MCP tools
- **Technology**: FastAPI-MCP client
- **Features**: Current time retrieval in UTC

## Features

### 🔒 Security
- Isolated code execution environment
- Package name validation and blocklist
- Suspicious package detection
- Container-based isolation
- Non-root execution in containers

### 🛠️ Available Tools
- **Code Execution**: Execute Python code in secure sandbox
- **Package Installation**: Install Python packages with security checks  
- **Time Services**: Get current time in UTC format

### 🌐 Integration
- OpenAI/Ollama LLM integration
- MCP protocol compliance
- RESTful API endpoints
- Prometheus metrics
- Health monitoring

### 📊 Monitoring
- Health check endpoints (`/health`, `/ready`)
- Prometheus metrics (`/metrics`)
- Service dependency monitoring
- CORS support for web interfaces

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Git

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp_things1

# Start all services
docker-compose up --build
```

### Service Endpoints

| Service | URL | Description |
|---------|-----|-------------|
| MCP Server | http://localhost:8000 | Main MCP coordinator |
| Middleware | http://localhost:8002 | Chat and LLM interface |
| Sandbox | http://localhost:8001 | Secure code execution |
| Time Client | http://localhost:8003 | Time-related tools |
| Code Executor | http://localhost:8004 | Code execution proxy |
| Prometheus | http://localhost:9090 | Metrics collection |
| Grafana | http://localhost:3000 | Metrics visualization |

### API Usage

#### Chat Interface
```bash
curl -X POST http://localhost:8002/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "What time is it?"}
    ]
  }'
```

#### Direct Code Execution
```bash
curl -X POST http://localhost:8001/execute \
  -H "Content-Type: application/json" \
  -d '{
    "code": "print(\"Hello from MCP Sandbox!\")"
  }'
```

#### Health Checks
```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:8001/health  
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health

# Check monitoring
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana (login: admin/admin)
```

## Development

### Project Structure
```
mcp_things1/
├── docker-compose.yml          # Service orchestration
├── mcp-server/                 # Main MCP server
│   ├── app/mcp_server/        # Server implementation
│   └── Dockerfile
├── middleware/                 # Chat and LLM integration
│   ├── app/main.py            # Middleware service
│   └── Dockerfile
├── sandbox/                   # Secure code execution
│   ├── app/main.py            # Sandbox implementation
│   └── Dockerfile
├── code-executor/             # Code execution MCP client
│   ├── app/main.py            # Client implementation
│   └── Dockerfile
├── time-client/               # Time tools MCP client
│   ├── app/time_client/       # Time tool implementation
│   └── Dockerfile
├── workspace/                 # Shared workspace volume
├── examples/                  # Usage examples
└── docs/                      # Documentation
```

### Configuration

Each service can be configured via environment variables:

#### MCP Server
- `PYTHONPATH`: Python module path

#### Middleware  
- `MCP_SERVER_URL`: MCP server endpoint
- `OPENAI_API_KEY`: OpenAI API key (if using OpenAI)
- `OPENAI_BASE_URL`: Custom OpenAI-compatible endpoint

#### Ollama Integration
The middleware supports Ollama running on the host:
- Default URL: `http://host.docker.internal:11434`
- Automatic health monitoring

### Development Workflow

1. **Start services in development mode**:
   ```bash
   docker-compose up --build
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f <service-name>
   ```

3. **Rebuild specific service**:
   ```bash
   docker-compose build <service-name>
   docker-compose up -d <service-name>
   ```

4. **Access container for debugging**:
   ```bash
   docker-compose exec <service-name> bash
   ```

## Security Considerations

### Code Execution Security
- Containerized execution environment
- Package validation and blocklists
- Execution timeouts
- Resource limits
- Non-root user execution

### Network Security
- Service isolation via Docker networks
- Health check validation
- CORS configuration
- Input validation

### Package Security
- Blocked malicious packages
- Suspicious package detection
- Version pinning support
- Installation timeouts

## Monitoring and Observability

### Health Endpoints
All services expose standard health endpoints:
- `/health`: Basic health status
- `/ready`: Readiness probe
- `/metrics`: Prometheus metrics (where applicable)

### Metrics
- Tool execution time and count
- Service health status
- Request/response tracking

### Logging
- Structured logging across all services
- Request/response logging
- Error tracking and reporting

## Deployment

### Local Development
Use Docker Compose as shown above.

### Production (Kubernetes)
The architecture supports Kubernetes deployment with:
- Sidecar pattern for MCP services
- Horizontal Pod Autoscaling
- Service mesh integration
- Persistent volume claims for workspace

### Environment Variables
- Configure via `.env` file or environment
- Secrets management via Docker secrets or K8s secrets
- Health check configurations

## Future Roadmap

See [IDEAS.md](IDEAS.md) for planned features:
- User authentication and authorization
- Jira, Mattermost, Confluence integrations
- Image generation tools
- Kubernetes query tools
- Markdown to PDF conversion
- API documentation discovery

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Architecture Documentation

For detailed architecture information, see:
- [Architecture Overview](mcp_architecture.md)
- [Sequence Diagrams](sequence_diagram.md)  
- [Docker Build Patterns](docker-build-pattern.md)
- [Development Ideas](IDEAS.md) 