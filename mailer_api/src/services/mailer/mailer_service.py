import http
import os
import smtplib
from email.message import EmailMessage

import requests
from fastapi import Depends
from jinja2 import Environment, FileSystemLoader

from auth_service.src.services.auth.users import UserService, get_user_service
from mailer_api.src.core import settings


class MailerService:
    async def send(
        self,
        domain: str,
        token,
        email_params: dict,
    ):
        if domain == "yandex.ru":
            host = settings.yandex.yandex_host
            port = settings.yandex.yandex_port
            login = settings.yandex.yandex_login
            password = settings.yandex.yandex_password
        user_service = await anext(get_user_service())
        server = smtplib.SMTP_SSL(host, port)
        email = f'{login}'
        server.login(login, password)



        current_path = os.path.dirname(__file__)
        loader = FileSystemLoader(current_path + "/mail_templates")
        env = Environment(loader=loader)

        films_config = {
            "film_id": {
                "fields": {
                    "film_name": "title",
                }
            },
            "episode_id": {
                "fields": {
                    "episode_name": "title",
                    "film_name": "series_title",
                }
            }
        }
        for param, data in films_config.items():
            if email_params["email_values"].get(param, None):
                url = (
                    settings.urls.films_url
                    + "/"
                    + email_params["email_values"][param]
                )
                headers = {"Authorization": "Bearer " + token}
                response = requests.get(url, headers=headers)
                if response.status_code != http.HTTPStatus.OK:
                    return None
                film_data = response.json()
                for email_field, field in data["fields"].items():
                    email_params["email_values"][email_field] = (
                        film_data[field]
                    )

        for email_to in email_params["to"]:
            message = EmailMessage()
            message["From"] = email
            message["Subject"] = email_params["subject"]
            template = env.get_template(email_params["template"] + ".html")
            user_to = await user_service.get_by_email(email_to)
            email_params["email_values"]["user_name"] = user_to["email"]

            output = template.render(**email_params["email_values"])
            message.add_alternative(output, subtype="html")
            print(email_to)
            message["To"] = ",".join([email_to])

            try:
                server.sendmail(email, [email_to], message.as_string())
            except smtplib.SMTPException as exc:
                reason = f'{type(exc).__name__}: {exc}'
                print(f'Не удалось отправить письмо. {reason}')
            else:
                print('Письмо отправлено!')

        server.close()
        return True


mailer_service = MailerService()


async def get_mailer_service():
    yield mailer_service
