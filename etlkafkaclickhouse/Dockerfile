FROM python:3.13

WORKDIR /opt/etl

COPY . .

RUN pip install -r /opt/etl/common/requirements.txt

ENTRYPOINT ["python", "/opt/etl/etl.py"]
