FROM python:3.13 AS base
RUN apt-get update && apt-get install -y \
    vim \
    iputils-ping

WORKDIR /opt
ENV PYTHONPATH=/opt
COPY ./pyproject.toml ./pyproject.toml

FROM base AS stage_one
WORKDIR /opt
# RUN pip install --no-cache-dir --upgrade -r requirements.txt
RUN pip install --upgrade pip
RUN pip install .

COPY . .

ENTRYPOINT ["sh", "-c", "ALEMBIC_CONFIG=/opt/fastapi_solution/src/alembic.ini alembic upgrade head && fastapi run /opt/fastapi_solution/src/main.py --proxy-headers --port 8000"]
