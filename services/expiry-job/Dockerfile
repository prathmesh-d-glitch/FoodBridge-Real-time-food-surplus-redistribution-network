FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/shared /app/services/shared
RUN pip install --no-cache-dir -e /app/services/shared

COPY services/expiry-job/requirements.txt /app/services/expiry-job/
RUN pip install --no-cache-dir -r /app/services/expiry-job/requirements.txt

COPY services/expiry-job/app /app/services/expiry-job/app

ENV PORT=8006
ENV PYTHONPATH=/app/services/expiry-job:/app/services/shared

EXPOSE 8006

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8006"]
