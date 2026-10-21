FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/shared /app/services/shared
RUN pip install --no-cache-dir -e /app/services/shared

COPY services/notification-service/requirements.txt /app/services/notification-service/
RUN pip install --no-cache-dir -r /app/services/notification-service/requirements.txt

COPY services/notification-service/app /app/services/notification-service/app

ENV PORT=8003
ENV PYTHONPATH=/app/services/notification-service:/app/services/shared

EXPOSE 8003

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8003"]
