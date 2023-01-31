import json
import threading
import time
from urllib.parse import urljoin

import redis
import requests

import modules.shared
from config import Config


def set_heartbeat():
    while True:
        try:
            requests.post(
                Config.API_URL,
                "/workers/status",
                data=json.dumps(modules.shared.message),
            )
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.InvalidSchema,
            requests.exceptions.MissingSchema,
            requests.exceptions.InvalidURL,
        ):
            pass
        time.sleep(5)


def start_heartbeat():
    x = threading.Thread(target=set_heartbeat)
    x.daemon = True
    x.start()
