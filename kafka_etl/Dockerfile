FROM python:3.13

COPY ./kafka_etl/requirements.txt /opt/requirements.txt

WORKDIR /opt

RUN pip install -r requirements.txt

COPY . /opt

COPY ./common /opt/kafka_etl/common

ENTRYPOINT ["python", "/opt/kafka_etl/etl.py"]
