import time

import requests

if __name__ == "__main__":
    max_retries = 10
    delay = 5
    retries = 0

    while retries < max_retries:
        try:
            response = requests.get("http://nginx/api/v1/auth")
            if 500 <= response.status_code < 600:
                retries += 1
                time.sleep(delay)
            else:
                break
        except requests.exceptions.RequestException:
            retries += 1
            time.sleep(delay)
