FROM python:3.11-slim

WORKDIR /app
ENV PYTHONPATH=/opt

COPY ugc_api/pyproject.toml ugc_api/poetry.lock ./

RUN pip install --no-cache-dir "poetry==2.1.3" && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --no-interaction --no-ansi --without dev

COPY ./ugc_api .

COPY ./common ./common

CMD ["sh", "-c", "fastapi run /app/src/main.py --proxy-headers --port 8000 "]

# CMD ["gunicorn", "src.main:app", \
#     "--workers", "4", \
#     "--worker-class", "uvicorn.workers.UvicornWorker", \
#     "--bind", "0.0.0.0:8000", \
#     "--timeout", "600", \
#     "--proxy-protocol", \
#     "--forwarded-allow-ips", "172.28.0.10"]