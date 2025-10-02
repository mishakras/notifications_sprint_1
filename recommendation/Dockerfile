FROM python:3.12-slim

WORKDIR /app

COPY ./recommendation/requirements.txt /app/requirements.txt

COPY ./auth_lib /app/auth_lib
COPY ./auth_service /app/auth_service

COPY ./recommendation/src /app/src

RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn", "src.main:app", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--bind", "0.0.0.0:8089", \
    "--timeout", "600", \
    "--proxy-protocol", \
    "--forwarded-allow-ips", "172.28.0.10"]