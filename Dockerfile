# syntax=docker/dockerfile:1.2
FROM python:3.13-slim as builder

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install only the essential build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy only necessary files for installing dependencies
COPY pyproject.toml README.md ./
COPY src ./src

# Create a virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install the package and dependencies
RUN pip install --no-cache-dir -e .

# Final stage - minimal runtime image
FROM python:3.13-slim

WORKDIR /app

# Install only the runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY --from=builder /app/src ./src
COPY pyproject.toml README.md ./

# Set Python path to include the src directory
ENV PYTHONPATH=/app:$PYTHONPATH

# Create README.md if it doesn't exist (just to be safe)
RUN touch README.md

# Run as non-root user for better security
RUN groupadd -g 1000 appuser && useradd -g appuser -u 1000 appuser
RUN mkdir -p /app/data && chown -R appuser:appuser /app

# Create directories for config volumes
RUN mkdir -p /app/src/config \
    /app/src/plugins/aissens/config \
    /app/src/tools/postgresql/config \
    /app/src/tools/sqlite/config \
    /app/src/tools/stdout/config \
    && chown -R appuser:appuser /app/src/config \
    /app/src/plugins \
    /app/src/tools

# Define volume mount points for configuration files
VOLUME /app/src/config
VOLUME /app/src/plugins/aissens/config
VOLUME /app/src/tools/postgresql/config
VOLUME /app/src/tools/sqlite/config
VOLUME /app/src/tools/stdout/config

USER appuser

ENV MPLCONFIGDIR=/app/data/matplotlib

# Set environment variables for sqlite data directory
ENV SQLITE_DATA_DIR=/app/src/tools/sqlite/data
ENV SQLITE_DB=sensor_data.db

# Create and set volume for persistent data
VOLUME /app/src/tools/sqlite/data

# PostgreSQL environment variables with default values
ENV POSTGRES_HOST=postgres
ENV POSTGRES_DB=sensor_data
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=postgres

# Command to run the application
CMD ["python", "-m", "src.main"]
