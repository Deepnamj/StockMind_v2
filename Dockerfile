
# Use Python 3.10
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Python configuration
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy dependencies first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the complete project
COPY . .

# FastAPI port
EXPOSE 10000

# Start the FastAPI application
CMD ["sh", "-c", "uvicorn src.hitl.api:app --host 0.0.0.0 --port ${PORT:-10000}"]
