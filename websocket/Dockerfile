FROM python:3.13

COPY ./websocket/requirements.txt /opt/requirements.txt

WORKDIR /opt

RUN pip install -r requirements.txt

COPY ./auth_lib /opt/auth_lib
COPY ./auth_service /opt/auth_service

COPY ./websocket /opt/websocket
COPY ./common /opt/common

ENTRYPOINT ["sh","-c", "fastapi run /opt/websocket/src/main.py --proxy-headers --port 8000"]
