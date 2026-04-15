FROM python:3.9-slim

# Install Chromium and ChromeDriver (works on both amd64 and arm64)
RUN apt-get update && apt-get install -y --no-install-recommends \
        chromium \
        chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /webapp

# Install Python deps before copying source for better layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /webapp

CMD ["python", "run.py"]
