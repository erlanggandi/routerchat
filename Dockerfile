FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies (including fonts for matplotlib graph rendering)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libffi-dev \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create data directory for SQLite persistence
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 3010

# Run entry point
CMD ["python", "-m", "app.main"]
