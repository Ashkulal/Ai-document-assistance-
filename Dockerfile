FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 1000

CMD gunicorn web_app:app --bind 0.0.0.0:1000 --workers 1 --timeout 120
