FROM python:3.13

COPY ./mongo_db_user_api/requirements.txt /opt/requirements.txt

WORKDIR /opt

RUN pip install -r requirements.txt

COPY ./auth_lib /opt/auth_lib
COPY ./auth_service /opt/auth_service

COPY ./mongo_db_user_api /opt/mongo_db_user_api

COPY ./common /opt/common

ENTRYPOINT ["sh","-c", "fastapi run /opt/mongo_db_user_api/src/main.py --proxy-headers --port 8000"]
