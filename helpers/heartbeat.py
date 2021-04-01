import redis
import time
import modules.shared
import threading

from config import Config


def set_heartbeat():
    r = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB
    )
    while True:
        try:
            r.set(f'worker:{Config.HOST_UUID}', modules.shared.message, ex=10)
        except (redis.exceptions.ConnectionError, ConnectionRefusedError):
            pass
        time.sleep(5)


def start_heartbeat():
    x = threading.Thread(target=set_heartbeat)
    x.daemon = True
    x.start()
