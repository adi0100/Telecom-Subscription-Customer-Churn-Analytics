FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy all project files into the container
COPY . /app/

# Collect static files
RUN python customerchurn/manage.py collectstatic --noinput || true

EXPOSE 8000

# Start Gunicorn server pointing to customerchurn WSGI module
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--chdir", "customerchurn", "customerchurn.wsgi:application"]