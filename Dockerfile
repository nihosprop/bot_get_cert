# Stage 0: Build dependencies
FROM python:3.13.1-slim-bullseye AS base
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache -r requirements.txt

# Stage 1: Add application code
FROM base
COPY . /app
CMD ["python", "main.py"]