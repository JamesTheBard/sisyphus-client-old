import json
import redis
from box import Box
from modules.exceptions import JobConfigurationError

import modules.shared
from config import Config


class BaseModule:

    data: Box
    job_title: str
    redis: redis.Redis

    def __init__(self, job_data: dict, job_title: str):
        try:
            self.data = Box(job_data)
        except KeyError as e:
            raise JobConfigurationError(
                message=f"Required variable '{e.args[0]}' is not defined, exiting.",
                module='base'
            )
        self.job_title = job_title
        self.redis = redis.Redis(host=Config.REDIS_HOST, port=Config.REDIS_PORT, db=Config.REDIS_DB)

    def run(self):
        pass

    def validate(self):
        pass

    @staticmethod
    def set_status(status: str = 'in_progress', job_title: str = None, job_id: str = None):
        message = {'hostname': Config.HOSTNAME, 'status': status}
        if job_title:
            message['job_title'] = job_title
        if job_id:
            message['job_id'] = job_id
        modules.shared.message = json.dumps(message)

    def update_progress(self, info: dict, expiration: int = 10):
        self.redis.set(f'progress:{Config.HOST_UUID}', json.dumps(info), ex=expiration)


