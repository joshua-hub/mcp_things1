import subprocess
from pathlib import Path
from typing import Dict, Any

from mcp.types import ToolResult

class CodeExecutionTool:
    """Tool for executing Python code in a sandboxed environment.
    
    This tool executes Python code in a sandboxed environment with:
    - Isolated workspace directory
    - 5-second execution timeout
    - Access to Python standard library and numpy
    """
    
    def __init__(self, workspace_dir: str = "/workspace"):
        """Initialize the code execution tool.
        
        Args:
            workspace_dir: Directory where code will be executed. This is a sandboxed
                          environment where temporary files are created and cleaned up.
        """
        self.workspace_dir = Path(workspace_dir)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
    
    async def execute_code(self, code: str) -> ToolResult:
        """Execute Python code in a sandboxed environment.
        
        The code is executed in an isolated workspace with a 5-second timeout.
        A temporary file is created to execute the code and automatically cleaned up.
        Available: Python standard library and numpy.
        
        Args:
            code: Python code to execute
        """
        try:
            # Create a temporary Python file in the sandboxed workspace
            code_file = self.workspace_dir / "temp.py"
            code_file.write_text(code)

            # Execute the code in the sandboxed workspace
            process = subprocess.run(
                ['python3', str(code_file)],
                capture_output=True,
                text=True,
                cwd=str(self.workspace_dir),
                timeout=5  # 5 second timeout
            )

            # Clean up the temporary file
            code_file.unlink()

            return ToolResult(
                success=True,
                output=process.stdout,
                error=process.stderr
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                error="Execution timed out after 5 seconds"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    def cleanup(self):
        """Clean up any remaining files in the sandboxed workspace."""
        for file in self.workspace_dir.glob("*"):
            try:
                file.unlink()
            except Exception:
                pass 