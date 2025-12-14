FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps (kept minimal). Add build tools here only if some wheels require it.
RUN apt-get update \
    && apt-get install -y --no-install-recommends bash ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the project
COPY . /app

# Ensure entrypoint is executable
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"]