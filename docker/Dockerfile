FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements - CHECK IF THIS FILE EXISTS!
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY .env.example .env

# Create audio directory
RUN mkdir -p /tmp/audio && chmod 777 /tmp/audio

# Expose port
EXPOSE $PORT

# Run the application
CMD uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
