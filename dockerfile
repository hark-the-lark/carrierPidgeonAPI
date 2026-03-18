# Dockerfile
FROM python:3.12-slim

# Install basic dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire repo
COPY . .

# Expose the port
EXPOSE 8000

# Command to run FastAPI
CMD ["python", "-m", "uvicorn", "service.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
