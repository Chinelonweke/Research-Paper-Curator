FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create audio directory
RUN mkdir -p /tmp/audio && chmod 777 /tmp/audio

# Expose port (optional, doesn't actually do anything on Heroku)
EXPOSE $PORT

# Run application - USE /bin/sh -c TO EXPAND $PORT
CMD /bin/sh -c "uvicorn src.api.main:app --host 0.0.0.0 --port $PORT"
