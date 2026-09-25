FROM mcr.microsoft.com/playwright/python:v1.47.0-jammy

RUN apt-get update && apt-get install -y --no-install-recommends fonts-dejavu-core libcairo2 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY bot ./bot
COPY assets ./assets

CMD ["python", "-m", "bot.main"]
