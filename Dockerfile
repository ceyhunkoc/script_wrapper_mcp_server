FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/workspace/src

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-venv \
    python3-pip \
    bash \
    curl \
    wget \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /workspace

# Copy requirements first for better caching
COPY requirements.txt pyproject.toml ./
COPY src/ ./src/

# Install Python dependencies
RUN python3.11 -m pip install --no-cache-dir --upgrade pip setuptools wheel
RUN python3.11 -m pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

# Create non-root user
RUN useradd -m -s /bin/bash mcpuser && chown -R mcpuser:mcpuser /workspace
USER mcpuser

# Create default configuration if it doesn't exist
RUN if [ ! -f .mcp-config.json ]; then \
    echo '{"working_directory": ".", "scripts": {}, "docker_image": "ubuntu:22.04", "container_name": "mcp-script-runner", "mount_path": "/workspace"}' > .mcp-config.json; \
    fi

# Expose port (if needed for future extensions)
EXPOSE 8080

# Set entrypoint
ENTRYPOINT ["./docker-entrypoint.sh"]