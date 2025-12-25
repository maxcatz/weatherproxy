FROM python:3.9-slim

RUN adduser --disabled-password appuser
WORKDIR /app
ENV PYTHONPATH=/app

RUN pip install --upgrade pip setuptools wheel
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
