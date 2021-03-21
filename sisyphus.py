import importlib
import json
import logging
import redis
import signal
import sys
import time
from box import Box
from datetime import datetime

import modules.shared
from config import Config
from helpers.heartbeat import start_heartbeat
from modules.exceptions import JobValidationError, JobRunFailureError, JobConfigurationError


def main():
    signal.signal(signal.SIGINT, graceful_exit)
    configure_logging()
    startup_message()
    update_status_message('startup')
    time.sleep(5)
    start_heartbeat()
    process_queue()


def update_status_message(status: str, job_title: str = None, job_id: str = None):
    message = {'status': status, 'hostname': Config.HOSTNAME}
    if job_title:
        message['job_title'] = job_title
    if job_id:
        message['job_id'] = job_id
    modules.shared.message = json.dumps(message)


def configure_logging():
    message_format = "[%(asctime)s] %(levelname)-8s %(message)s"
    # noinspection PyArgumentList
    logging.basicConfig(
        level="INFO",
        format=message_format, datefmt="[%x %X]",
    )


def startup_message():
    logging.info(f"Starting worker version {Config.VERSION}")
    logging.debug(f"REDIS: Server 'redis://{Config.REDIS_HOST}:{Config.REDIS_PORT}/{Config.REDIS_DB}'")
    logging.debug(f"REDIS: Monitoring queue '{Config.REDIS_QUEUE_NAME}'")
    logging.info(f"Hostname:  '{Config.HOSTNAME}'")
    logging.info(f"Worker ID: '{Config.HOST_UUID}'")


def get_job() -> Box:
    r = redis.Redis(
        host=Config.REDIS_HOST,
        port=Config.REDIS_PORT,
        db=Config.REDIS_DB,
    )
    if job := r.rpop(Config.REDIS_QUEUE_NAME):
        return Box(json.loads(job))
    return Box()


def process_queue():
    logging.info("Worker online, ready to process jobs.")
    been_waiting = False
    while True:
        time.sleep(1)
        if job := get_job():
            job_failed = False
            job_start_time = datetime.now()
            been_waiting = False
            job_title = job.pop('job_title')
            job_id = job.pop('job_id')
            job_tasks = list(job.keys())
            job_tasks_str = ' -> '.join(job_tasks)
            update_status_message('in_progress', job_title, job_id)
            logging.info(f"ACCEPTED JOB: {job_title}: {job_id}")
            logging.info(f" + [{job_title}] Tasks in job: {job_tasks_str}")
            for task, data in job.items():
                task_start_time = datetime.now()
                module_path = f'modules.{task}'
                try:
                    module = getattr(importlib.import_module(module_path), task.capitalize())
                except (AttributeError, ModuleNotFoundError):
                    logging.critical(f" ! [{job_title}:{task}] TASK FAILED: Could not load module, abandoning task.")
                    logging.critical(f"JOB FAILED: {job_title}: {job_id}")
                    job_failed = True
                    break
                logging.info( f" + [{job_title}] Successfully loaded module: {task}")
                logging.debug(f" + [{job_title}:{task}] Validating data: '{data}'")
                task_instance = module(data=data, job_title=job_title)
                try:
                    task_instance.validate()
                    logging.info(f" + [{job_title}:{task}] Running task from module...")
                    task_instance.run()
                except (JobValidationError, JobRunFailureError, JobConfigurationError) as e:
                    logging.critical(f" ! [{job_title}:{task}] {type(e).__name__}: {e.message}")
                    logging.critical(f"JOB FAILED: {job_title}: {job_id}")
                    job_failed = True
                    break
                task_run_time = datetime.now() - task_start_time
                logging.info(f" + [{job_title}:{task}] Completed task in '{task_run_time}'.")
            if not job_failed:
                logging.info(f"COMPLETED JOB: {job_title}: {job_id}")
                job_run_time = datetime.now() - job_start_time
                logging.info(f"DURATION: {job_run_time}")
        else:
            if not been_waiting:
                logging.info(f"Waiting for job in Redis queue '{Config.REDIS_QUEUE_NAME}'")
                been_waiting = True
            update_status_message('idle')


def graceful_exit(_sig, _frame):
    logging.info("Exiting the program due to SIGINT")
    sys.exit(1)


if __name__ == "__main__":
    main()
