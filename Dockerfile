FROM python:3.9-slim
RUN apt-get update && \
    apt-get install -y certbot && \
    rm -rf /var/lib/apt/lists/*
RUN pip install docker apscheduler
WORKDIR /app
COPY ssl_renew.py /app/ssl_renew.py
CMD ["python", "/app/ssl_renew.py"]