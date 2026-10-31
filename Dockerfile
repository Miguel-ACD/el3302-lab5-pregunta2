FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PYTHONUNBUFFERED=1 PORT=8000
EXPOSE 8000
CMD ["gunicorn", "--workers", "2", "--timeout", "30", "--bind", "0.0.0.0:8000", "app.web:create_app()"]
