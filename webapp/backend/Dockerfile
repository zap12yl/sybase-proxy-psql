# In webapp/backend/Dockerfile
FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    unixodbc-dev \
    freetds-dev \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install migration package from root directory
COPY migration ./migration
RUN pip install --no-cache-dir ./migration

# Then install backend requirements
COPY ./webapp/backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./webapp/backend/src/ ./src/

ENV PYTHONPATH="${PYTHONPATH}:/app"

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
