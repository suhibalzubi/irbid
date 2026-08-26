# Dockerfile for backend
FROM python:3.11-slim
WORKDIR /app

# Install system deps for weasyprint (if later used)
RUN apt-get update && apt-get install -y build-essential libffi-dev libxml2 libxml2-dev libxslt1-dev libjpeg-dev zlib1g-dev libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2 && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend /app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
