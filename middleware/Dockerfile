FROM python:3.12-alpine AS builder

# Install build dependencies
RUN apk add --no-cache \
    python3-dev \
    build-base \
    libffi-dev

# Set up pip configuration
COPY pip.conf /root/.pip/pip.conf

# Create and activate virtual environment
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

# Install Python dependencies
COPY middleware/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.12-alpine

# Install only essential runtime dependencies
RUN apk add --no-cache \
    libstdc++ \
    # Create non-root user
    && addgroup -S appgroup \
    && adduser -S -G appgroup -h /app appuser \
    # Create workspace directory
    && mkdir -p /app/workspace \
    && chown -R appuser:appgroup /app \
    # Remove unnecessary packages
    && rm -rf /var/cache/apk/*

# Copy only the virtual environment from builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Set up application directory
WORKDIR /app

# Copy application code with correct ownership
COPY --chown=appuser:appgroup middleware/app/ /app/

# Clean up the virtual environment and remove shells for security
RUN find /venv -type f -name "*.so" -exec strip {} \; 2>/dev/null || true \
    && find /venv -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true \
    && find /venv -type f -name "*.pyc" -delete \
    && find /venv -type d -name "*.egg-info" -exec rm -r {} + 2>/dev/null || true \
    && find /venv -type d -name "doc" -exec rm -r {} + 2>/dev/null || true \
    && find /venv -type d -name "docs" -exec rm -r {} + 2>/dev/null || true \
    && rm -f /bin/sh /bin/ash /bin/bash \
    && rm -rf /bin/* /sbin/* /usr/bin/* /usr/sbin/* 2>/dev/null || true

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH="/venv/lib/python3.12/site-packages" \
    HOME="/app" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Run the server using full path to Python interpreter
CMD ["/venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"] 