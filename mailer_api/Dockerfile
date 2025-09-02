FROM python:3.13

COPY ./mongo_db_user_api/requirements.txt /opt/requirements.txt

WORKDIR /opt

RUN pip install -r requirements.txt

COPY ./auth_service /opt/auth_service
COPY ./auth_lib /opt/auth_lib
COPY ./mailer_api /opt/mailer_api

COPY ./common /opt/common

ENTRYPOINT ["sh","-c", "fastapi run /opt/mailer_api/src/main.py --proxy-headers --port 8001"]
