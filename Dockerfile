FROM python:3.11-slim

WORKDIR /app
COPY . /app

# speed up pip
ENV PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y gcc libsndfile1 curl && rm -rf /var/lib/apt/lists/*

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

EXPOSE 8080
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
