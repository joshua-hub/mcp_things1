# MCP Code Execution Server

A secure code execution environment built using the Model Context Protocol (MCP). This project provides a server implementation for executing Python code and managing package installations in a secure, isolated environment.

## Features

- Secure code execution in an isolated environment
- Package installation management with security checks
- MCP protocol implementation for standardized communication
- Built-in security measures against malicious packages
- Example client implementation
- Docker containerization for easy deployment

## Installation

### Local Installation

```bash
# Install the package
pip install -e .

# Install development dependencies
pip install -e ".[dev]"
```

### Docker Installation

```bash
# Build the Docker image
docker build -t mcp-code-execution-server .

# Run the container
docker run -it mcp-code-execution-server
```

## Usage

### Running the Server

#### Local
```bash
python -m mcp_code_execution_server
```

#### Docker
```bash
docker run -it mcp-code-execution-server
```

### Using the Client

A simple client example is provided in `examples/client.py`:

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_code_execution_server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Execute code
            result = await session.call_tool(
                "execute_code",
                arguments={"code": "print('Hello, World!')"}
            )
            
            # Install package
            result = await session.call_tool(
                "install_package",
                arguments={"package": "requests", "version": "2.31.0"}
            )

if __name__ == "__main__":
    asyncio.run(main())
```

## Available Tools

### Execute Code
- **Tool Name**: `execute_code`
- **Description**: Executes Python code in a secure environment
- **Arguments**:
  - `code`: The Python code to execute

### Install Package
- **Tool Name**: `install_package`
- **Description**: Installs Python packages with security validation
- **Arguments**:
  - `package`: Name of the package to install
  - `version`: Version of the package (optional, defaults to "latest")

## Security Features

- Package name validation
- Blocked malicious packages list
- Suspicious packages requiring approval
- Execution timeout limits (5 seconds for code, 60 seconds for package installation)
- Isolated workspace environment
- Secure container configuration
- Non-root user execution in container

## Project Structure

```
mcp-code-execution-server/
├── mcp_code_execution_server/
│   ├── __init__.py
│   ├── __main__.py
│   └── server.py
├── examples/
│   └── client.py
├── Dockerfile
├── pyproject.toml
└── README.md
```

## Development

1. Clone the repository
2. Install development dependencies: `pip install -e ".[dev]"`
3. Run tests: `pytest`
4. Run linting: `ruff check .`

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 