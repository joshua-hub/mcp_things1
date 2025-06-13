from datetime import datetime, timezone
from mcp.types import ToolResult

class TimeTool:
    """Tool for getting current time information."""
    
    async def get_current_time(self) -> ToolResult:
        """Get the current time in UTC ISO format. This function returns the time in UTC, which is a standardized time format.
        
        Returns:
            Current time in UTC ISO format
        """
        current_time = datetime.now(timezone.utc).isoformat() + " UTC"
        return ToolResult(
            success=True,
            output=current_time
        ) 