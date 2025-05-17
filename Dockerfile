FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    pkg-config \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY . .

# Set environment variable
ENV PYTHONPATH=/app

# Copy the start.sh script
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Use shell form to ensure $PORT is interpreted
CMD ["/bin/bash", "/start.sh"]
