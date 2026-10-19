FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install shared package first
COPY services/shared /app/services/shared
RUN pip install --no-cache-dir -e /app/services/shared

# Install listing-service dependencies
COPY services/listing-service/requirements.txt /app/services/listing-service/
RUN pip install --no-cache-dir -r /app/services/listing-service/requirements.txt

# Copy service code
COPY services/listing-service/app /app/services/listing-service/app

ENV PORT=8001
ENV PYTHONPATH=/app/services/listing-service:/app/services/shared

EXPOSE 8001

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
