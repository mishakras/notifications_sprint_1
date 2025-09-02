FROM python:3.13


COPY ./requirements.txt /opt/requirements.txt

WORKDIR /opt

RUN pip install -r requirements.txt

COPY . /opt

ENTRYPOINT ["python", "manage.py", "runserver", "0.0.0.0:8000"]
