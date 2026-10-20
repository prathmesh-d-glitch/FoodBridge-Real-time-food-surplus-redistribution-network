FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/shared /app/services/shared
RUN pip install --no-cache-dir -e /app/services/shared

COPY services/logistics-service/requirements.txt /app/services/logistics-service/
RUN pip install --no-cache-dir -r /app/services/logistics-service/requirements.txt

COPY services/logistics-service/app /app/services/logistics-service/app

ENV PORT=8004
ENV PYTHONPATH=/app/services/logistics-service:/app/services/shared

EXPOSE 8004

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8004"]
