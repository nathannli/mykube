# Dockerfile
FROM python:3.13-slim

# Install curl and any system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alert_bot.py .

CMD ["python", "alert_bot.py"]