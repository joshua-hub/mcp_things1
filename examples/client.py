import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    # Create server parameters for stdio connection
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "mcp_code_execution"],
        env=None,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Available tools:", tools)

            # Execute some Python code
            result = await session.call_tool(
                "execute_code",
                arguments={
                    "code": "print('Hello from MCP code execution!')"
                }
            )
            print("\nCode execution result:")
            print("Success:", result.success)
            print("Output:", result.output)
            print("Error:", result.error)

            # Try to install a package
            result = await session.call_tool(
                "install_package",
                arguments={
                    "package": "requests",
                    "version": "2.31.0"
                }
            )
            print("\nPackage installation result:")
            print("Success:", result.success)
            print("Output:", result.output)
            print("Error:", result.error)

if __name__ == "__main__":
    asyncio.run(main()) 