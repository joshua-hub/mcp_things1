from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, constr
import subprocess
import os
from pathlib import Path
import re
import uvicorn

app = FastAPI()

WORKSPACE_DIR = Path("/app/workspace")

# Package name validation regex
PACKAGE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9\-_\.]+$')

# Known malicious or problematic packages
BLOCKED_PACKAGES = {
    'crypto-locker',
    'pythonapi',
    'python-api',
    'system',
    'snake',
    # Add more as needed
}

# Packages that require extra scrutiny
SUSPICIOUS_PACKAGES = {
    'cryptography',
    'crypto',
    'requests',
    'urllib3',
    'socket',
    'subprocess',
    # Add more as needed
}

class CodeRequest(BaseModel):
    code: str

class PipRequest(BaseModel):
    package: constr(min_length=1, max_length=100)  # Constrain package name length
    version: str = "latest"

class CodeResponse(BaseModel):
    success: bool
    output: str = ""
    error: str = ""

def validate_package_name(package: str) -> bool:
    """Validate package name against security rules."""
    if package.lower() in BLOCKED_PACKAGES:
        raise HTTPException(status_code=400, detail=f"Package {package} is blocked for security reasons")
    
    if not PACKAGE_NAME_PATTERN.match(package):
        raise HTTPException(status_code=400, detail="Invalid package name format")
    
    if package.lower() in SUSPICIOUS_PACKAGES:
        raise HTTPException(status_code=400, detail=f"Package {package} requires administrative approval")
    
    return True

@app.post("/execute", response_model=CodeResponse)
async def execute_code(request: CodeRequest):
    try:
        # Create a temporary Python file in the workspace
        code_file = WORKSPACE_DIR / "temp.py"
        code_file.write_text(request.code)

        # Execute the code and capture output
        process = subprocess.run(
            ['python3', str(code_file)],
            capture_output=True,
            text=True,
            cwd=str(WORKSPACE_DIR),
            timeout=5  # 5 second timeout
        )

        # Clean up
        code_file.unlink()

        return CodeResponse(
            success=True,
            output=process.stdout,
            error=process.stderr
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=400,
            detail="Execution timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

@app.post("/pip/install", response_model=CodeResponse)
async def pip_install(request: PipRequest):
    try:
        # Validate package name
        validate_package_name(request.package)
        
        # Construct pip command
        pip_cmd = ['pip', 'install', '--no-cache-dir']
        if request.version != "latest":
            pip_cmd.append(f"{request.package}=={request.version}")
        else:
            pip_cmd.append(request.package)

        # Run pip install
        process = subprocess.run(
            pip_cmd,
            capture_output=True,
            text=True,
            timeout=60  # 1 minute timeout for pip
        )

        return CodeResponse(
            success=process.returncode == 0,
            output=process.stdout,
            error=process.stderr
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    # Ensure workspace directory exists and is writable
    WORKSPACE_DIR.mkdir(exist_ok=True)
    uvicorn.run(app, host="0.0.0.0", port=5000) 