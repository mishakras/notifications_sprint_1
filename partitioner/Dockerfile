FROM python:3.13

WORKDIR /opt/partitioner

COPY ./common/requirements.txt ./common/requirements.txt

RUN pip install -r /opt/partitioner/common/requirements.txt

COPY . .

ENTRYPOINT [ "python", "/opt/partitioner/main.py" ]
