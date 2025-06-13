# Stage 1: Builder
FROM python:3.10-alpine as builder

# Install build dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Stage 2: Final
FROM python:3.10-alpine

# Install runtime dependencies
RUN apk add --no-cache \
    libffi \
    openssl

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN adduser -D -u 1000 appuser

# Create workspace directory
RUN mkdir -p /workspace && chown -R appuser:appuser /workspace

# Copy application code
COPY app /app
WORKDIR /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app
ENV MCP_ENABLED_TOOLS=code_execution,time

# Run the server
CMD ["python", "-m", "mcp_server"] 