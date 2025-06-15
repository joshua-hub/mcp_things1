# MCP Distributed System

A distributed Model Context Protocol (MCP) implementation featuring secure code execution, middleware orchestration, and microservices architecture. This project demonstrates a production-ready MCP system with multiple specialized services working together.

## Architecture Overview

The system consists of six main services orchestrated via Docker Compose:

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
- **Port**: 8001 (internal only)
- **Role**: Secure Python code execution environment  
- **Technology**: FastAPI-MCP with security controls
- **Features**: Code execution, package installation, security validation

### 💻 **Code Executor** (`code-executor`)
- **Port**: 8002 (internal only)
- **Role**: MCP client that forwards code execution to sandbox
- **Technology**: FastAPI-MCP client
- **Features**: Tool interface for code execution

### ⏰ **Time Client** (`time-client`)
- **Port**: 8003 (internal only)
- **Role**: Time-related MCP tools
- **Technology**: FastAPI-MCP client
- **Features**: Current time retrieval in UTC

### 🤖 **Ollama** (`ollama`)
- **Port**: 11434
- **Role**: Local LLM inference engine
- **Technology**: Ollama with GPU acceleration
- **Features**: Local model hosting, OpenAI-compatible API, model management

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
- NVIDIA GPU (optional, for Ollama acceleration)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp_things1

# Create data directories for persistent storage
mkdir -p data/grafana data/prometheus

# Start all services
docker-compose up --build
```

### Service Endpoints

**External Services**:

| Service | URL | Description |
|---------|-----|-------------|
| MCP Server | http://localhost:8000 | Main MCP coordinator |
| Middleware | http://localhost:8002 | Chat and LLM interface |
| Ollama | http://localhost:11434 | Local LLM inference |
| Prometheus | http://localhost:9090 | Metrics collection |
| Grafana | http://localhost:3000 | Metrics visualization |

**Internal Services** (no external access):

| Service | Internal Port | Description |
|---------|---------------|-------------|
| Sandbox | 8001 | Secure code execution |
| Time Client | 8003 | Time-related tools |
| Code Executor | 8002 | Code execution proxy |

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

#### Health Checks
```bash
# Check external services
curl http://localhost:8000/health  # MCP Server
curl http://localhost:8002/health  # Middleware

# Check monitoring
curl http://localhost:9090  # Prometheus
curl http://localhost:3000  # Grafana (login: admin/admin)

# Internal services (sandbox, time-client, code-executor) 
# are not accessible from host - they communicate via Docker network
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
├── data/                      # Persistent data (host mounts)
│   ├── grafana/               # Grafana data
│   └── prometheus/            # Prometheus data
├── monitoring/                # Monitoring configuration
│   ├── prometheus.yml         # Prometheus config
│   └── grafana/               # Grafana config
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
Ollama is integrated directly into the Docker Compose stack:
- **Service URL**: `http://ollama:11434`
- **GPU Support**: Automatic NVIDIA GPU detection and acceleration
- **Persistent Storage**: Models stored in `~/docker-data/ollama`
- **Health Monitoring**: Automatic health checks and dependency management
- **Configuration**: Uses OpenAI-compatible API at `/v1/chat/completions`

**Environment Variables**:
- `LLM_BASE_URL=http://ollama:11434/v1` (default)
- `LLM_API_KEY=ollama` (default)  
- `LLM_MODEL_NAME=llama3.1:latest` (default)

**Model Management**:
```bash
# Pull models via Ollama service
docker-compose exec ollama ollama pull llama3.1:latest
docker-compose exec ollama ollama list
```

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
- Automatic service isolation via Docker Compose default networking
- Service-to-service communication using service names as hostnames
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

## Storage and Networking

### Storage Architecture
The system uses **host bind mounts** instead of Docker volumes for better portability and data management:
- **Monitoring Data**: `./data/grafana`, `./data/prometheus` 
- **Ollama Models**: `~/docker-data/ollama` (user home directory)
- **Configuration Files**: Mounted read-only from host
- **Benefits**: Easy backup, direct file access, no Docker volume management

### Networking
Uses **Docker Compose default networking** for simplicity:
- All services communicate via service names (e.g., `http://ollama:11434`)
- No custom network configuration required
- Automatic service discovery and DNS resolution
- Container isolation with controlled inter-service communication

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