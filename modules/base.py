import json
import redis
from box import Box
from modules.exceptions import JobConfigurationError

import modules.shared
import box
from config import Config


class BaseModule:

    data: Box
    job_title: str
    redis: redis.Redis
    module_name: str

    def __init__(self, job_data: dict, job_title: str):
        self.data = Box(job_data)
        self.job_title = job_title
        self.redis = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)

    def run(self):
        pass

    def validate(self):
        pass

    def set_status(self, status: str = 'in_progress', **kwargs):
        message = {'status': status, 'hostname': Config.HOSTNAME, 'version': Config.VERSION, 'task': self.module_name}
        kwargs_filter = ["job_title", "job_id", "task"]
        for k, v in kwargs.items():
            if k in kwargs_filter:
                message[k] = str(v)
        modules.shared.message = json.dumps(message)

    def update_progress(self, info: dict, expiration: int = 10):
        self.redis.set(f'progress:{Config.HOST_UUID}', json.dumps(info), ex=expiration)


