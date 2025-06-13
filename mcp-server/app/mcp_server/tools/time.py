from datetime import datetime
from mcp.types import ToolResult

class TimeTool:
    """Tool for getting current time information."""
    
    async def get_current_time(self) -> ToolResult:
        """Get the current time in ISO format.
        
        Returns:
            Current time in ISO format
        """
        current_time = datetime.now().isoformat()
        return ToolResult(
            success=True,
            output=current_time
        ) 