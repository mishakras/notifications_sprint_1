import http
import json
from enum import StrEnum, auto

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend

User = get_user_model()


class Roles(StrEnum):
    Administrator = auto()
    SUBSCRIBER = auto()


class EmailAuthBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None):
        admin_found = False
        url = settings.AUTH_API_URL + "/login"
        payload = {"email": username, "password": password}

        response = requests.post(url, data=json.dumps(payload))
        if response.status_code != http.HTTPStatus.OK:
            return None

        token_data = response.json()
        token = token_data["access_token"]

        url = settings.AUTH_API_URL + "/user"
        headers = {"Authorization": "Bearer " + token}
        response = requests.get(url, headers=headers)
        if response.status_code != http.HTTPStatus.OK:
            return None

        user_data = response.json()

        if user_data["is_superuser"] and user_data["is_active"]:
            admin_found = True

        if not admin_found and user_data["is_active"]:
            url = settings.AUTH_API_URL + "/user/roles"
            response = requests.get(url, headers=headers)
            if response.status_code != http.HTTPStatus.OK:
                return None

            roles_data = response.json()
            for role_data in roles_data:
                if role_data["name"] == Roles.Administrator:
                    admin_found = True

        if admin_found:
            try:
                try:
                    user = User.objects.get(email=username)
                except User.DoesNotExist:
                    user = User(email=username)
                    user.is_superuser = True
                    user.save()
            except Exception:
                return None

            return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
