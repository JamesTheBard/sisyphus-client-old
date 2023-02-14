import json
from urllib.parse import urljoin

import requests
from box import Box

import modules.shared
from config import Config


class BaseModule:

    data: Box
    job_title: str
    module_name: str

    def __init__(self, job_data: dict, job_title: str):
        self.data = Box(job_data)
        self.job_title = job_title

    def run(self):
        pass

    def validate(self):
        pass

    def set_status(self, status: str = "in_progress", **kwargs):
        message = {
            "status": status,
            "hostname": Config.HOSTNAME,
            "version": Config.VERSION,
            "task": self.module_name,
        }
        kwargs_filter = ["job_title", "job_id", "task"]
        for k, v in kwargs.items():
            if k in kwargs_filter:
                message[k] = str(v)
        modules.shared.message = message

    def update_progress(self, info: dict):
        modules.shared.message['data'] = info
