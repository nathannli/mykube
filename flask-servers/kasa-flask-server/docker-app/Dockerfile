# Dockerfile
FROM python:3.14-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flask-app.py .
COPY config.py .
COPY my_logger.py .
COPY time_of_use_electricity_pricing.py .

EXPOSE 9100
CMD ["python", "-u", "flask-app.py"]