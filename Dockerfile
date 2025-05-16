FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Create and activate virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app

# Create a shell script to start the application
RUN echo '#!/bin/bash\nexec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"' > /app/start.sh && \
    chmod +x /app/start.sh

# Run the application
CMD ["/bin/bash", "/app/start.sh"]
