import time

from redis import Redis

if __name__ == "__main__":
    redis = Redis(host="redis", port=6379)
    while True:
        if redis.ping():
            break
        time.sleep(1)
