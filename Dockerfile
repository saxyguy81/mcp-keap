# Production Dockerfile for Keap MCP Service
FROM python:3.11-slim

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Create app user for security (never run as root in production)
RUN groupadd -r app && useradd -r -g app app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set work directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /app/logs /app/config && \
    chown -R app:app /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install production-specific dependencies
RUN pip install --no-cache-dir \
    uvloop>=0.17.0 \
    gunicorn>=21.0.0 \
    prometheus-client \
    structlog

# Copy application code with proper ownership
COPY --chown=app:app . .

# Create production configuration template
RUN echo '# Production Configuration Template\n\
# Copy this to .env and configure for your environment\n\
KEAP_API_KEY=your_api_key_here\n\
KEAP_API_BASE_URL=https://api.infusionsoft.com/crm/rest/v1\n\
ENABLE_OPTIMIZATIONS=true\n\
MAX_CONNECTIONS=50\n\
LOG_LEVEL=INFO\n\
CACHE_DB_PATH=/app/data/keap_cache.db\n\
' > /app/config/.env.template

# Switch to app user for security
USER app

# Health check command
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import asyncio; import httpx; asyncio.run(httpx.get('http://localhost:8000/health', timeout=5.0))" || exit 1

# Expose the application port
EXPOSE 8000

# Default command - can be overridden in docker-compose or k8s
CMD ["python", "run.py"]