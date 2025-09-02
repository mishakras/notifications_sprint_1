FROM python:3.13

COPY ./notification_service/requirements.txt /opt/requirements.txt

WORKDIR /opt

RUN pip install -r requirements.txt

COPY ./auth_lib /opt/auth_lib
COPY ./auth_service /opt/auth_service

COPY ./notification_service /opt/notification_service

COPY ./common /opt/common

ENTRYPOINT ["sh","-c", "fastapi run /opt/notification_service/src/main.py --proxy-headers --port 8000"]
