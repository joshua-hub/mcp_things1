FROM python:3.10-slim AS builder

# Install build dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3-venv \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Setup pip config for local mirror
COPY pip.conf /root/.pip/pip.conf

# Install Python dependencies
COPY sandbox/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-alpine

# Install only the absolute minimum runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    # Create non-root user
    && addgroup -S appgroup \
    && adduser -S -G appgroup -h /app appuser \
    # Remove unnecessary packages
    && rm -rf /var/cache/apk/* \
    # Remove shell and other utilities
    && rm -f /bin/sh /bin/ash /bin/bash \
    && rm -rf /bin/* /sbin/* /usr/bin/* /usr/sbin/* \
    # Keep only Python and our venv
    && mkdir -p /app/workspace \
    && chown -R appuser:appgroup /app

# Copy only the virtual environment from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Set up application directory
WORKDIR /app

# Copy application code with correct ownership
COPY --chown=appuser:appgroup sandbox/app/ /app/

# Remove debug symbols from Python binaries
RUN find /venv -type f -name "*.so" -exec strip {} \; 2>/dev/null || true

# Remove Python bytecode and documentation
RUN find /venv -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true \
    && find /venv -type f -name "*.pyc" -delete \
    && find /venv -type d -name "*.dist-info" -exec rm -r {} + 2>/dev/null || true \
    && find /venv -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true \
    && find /venv -type d -name "doc" -exec rm -r {} + 2>/dev/null || true \
    && find /venv -type d -name "docs" -exec rm -r {} + 2>/dev/null || true

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH="/venv/lib/python3.10/site-packages" \
    HOME="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Run the server using full path to Python interpreter
CMD ["/venv/bin/python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"] 