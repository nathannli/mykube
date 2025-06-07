# Dockerfile
FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY flask-app.py .

EXPOSE 9100
CMD ["python", "flask-app.py"]