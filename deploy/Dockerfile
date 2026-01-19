FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (libsodium for keri/pysodium)
RUN apt-get update && apt-get install -y \
    libsodium-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY src/ src/

# Install dependencies (increased timeout for slower networks)
ENV UV_HTTP_TIMEOUT=120
RUN uv pip install --system .

# Run uvicorn
EXPOSE 8000
CMD ["uvicorn", "kelp.web:app", "--host", "0.0.0.0", "--port", "8000"]
