FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/shared /app/services/shared
RUN pip install --no-cache-dir -e /app/services/shared

COPY services/analytics-service/requirements.txt /app/services/analytics-service/
RUN pip install --no-cache-dir -r /app/services/analytics-service/requirements.txt

COPY services/analytics-service/app /app/services/analytics-service/app

ENV PORT=8005
ENV PYTHONPATH=/app/services/analytics-service:/app/services/shared

EXPOSE 8005

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8005"]
