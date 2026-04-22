FROM python:3.12-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-client rsync curl ca-certificates unzip \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o /tmp/r.zip \
    && unzip -q /tmp/r.zip -d /tmp && mv /tmp/rclone-*-linux-amd64/rclone /usr/local/bin/rclone \
    && chmod +x /usr/local/bin/rclone && rm -rf /tmp/r.zip /tmp/rclone-*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
ENV PYTHONUNBUFFERED=1
EXPOSE 8000
