# Backend Dockerfile for Polymarket Trading Bot
FROM python:3.9.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy poly_data and related modules from parent directory
COPY ../poly_data /app/poly_data
COPY ../poly_merger /app/poly_merger
COPY ../poly_utils /app/poly_utils

# Install Node.js dependencies for merger
WORKDIR /app/poly_merger
RUN npm install

# Go back to app directory
WORKDIR /app

# Initialize database
RUN python database.py

# Expose port
EXPOSE 8000

# Run FastAPI with uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

