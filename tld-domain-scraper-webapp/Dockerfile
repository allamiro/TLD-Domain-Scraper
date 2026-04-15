FROM python:3.9-slim

WORKDIR /webapp

# Copy requirements first so this layer is cached unless dependencies change
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /webapp

CMD ["python", "run.py"]
