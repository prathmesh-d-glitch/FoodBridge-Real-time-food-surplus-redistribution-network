FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/shared /app/services/shared
RUN pip install --no-cache-dir -e /app/services/shared

COPY services/matching-service/requirements.txt /app/services/matching-service/
RUN pip install --no-cache-dir -r /app/services/matching-service/requirements.txt

COPY services/matching-service/app /app/services/matching-service/app

ENV PORT=8002
ENV PYTHONPATH=/app/services/matching-service:/app/services/shared

EXPOSE 8002

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]
