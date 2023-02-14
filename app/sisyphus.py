import importlib
import json
import logging
import signal
import sys
import time
from box import Box
from datetime import datetime
import requests
from urllib.parse import urljoin

import modules.shared
from config import Config
from helpers.heartbeat import start_heartbeat
from modules.exceptions import (
    JobValidationError,
    JobRunFailureError,
    JobConfigurationError,
    JobModuleInitError,
)

logger = logging.getLogger(__name__)

def main():
    signal.signal(signal.SIGINT, graceful_exit)
    configure_logging()
    startup_message()
    update_status_message(status="startup", task="startup")
    time.sleep(5)
    start_heartbeat()
    process_queue()


def update_status_message(status: str, **kwargs):
    message = {"status": status, "hostname": Config.HOSTNAME, "version": Config.VERSION}
    kwargs_filter = ["job_title", "job_id", "task"]
    for k, v in kwargs.items():
        if k in kwargs_filter:
            message[k] = str(v)
    modules.shared.message = message


# TODO: Fix logging (make it look nice)
def configure_logging():
    message_format = "%(asctime)s %(levelname)-8s %(message)s"
    # noinspection PyArgumentList
    logging.basicConfig(
        level="INFO",
        format=message_format,
        datefmt="[%x %X]",
    )


def startup_message():
    logging.info(f"Starting worker version {Config.VERSION}")
    logging.info(f"API Server: {Config.API_URL}")
    logging.info(f"Hostname  : {Config.HOSTNAME}")
    logging.info(f"Worker ID : {Config.HOST_UUID}")


def get_job() -> Box:
    try:
        if r := requests.get(urljoin(Config.API_URL, f"/disable/{Config.HOST_UUID}")):
            if r.status_code == 404:
                logging.info("Waiting for worker status from server...")
                time.sleep(Config.API_POLLING_DELAY)
                return Box()
            if r.status_code == 200:
                data = Box(json.loads(r.text))
                if data.disabled:
                    logging.info("Worker is disabled and cannot accept jobs!")
                    time.sleep(Config.API_POLLING_DELAY)
                    return Box()
        if r := requests.get(urljoin(Config.API_URL, "/queue/poll")):
            if r.status_code == 200:
                logging.info("New job found for worker!")
                return Box(json.loads(r.text))
            if r.status_code == 404:
                time.sleep(Config.API_POLLING_DELAY)
                return Box()
    except requests.exceptions.ConnectionError as e:
        if modules.shared.is_connected_to_api:
            logging.warning(f"Cannot connect to the API server: {str(e)}")
            modules.shared.is_connected_to_api = False
        time.sleep(Config.API_FAILURE_DELAY)
        return Box()
    except (requests.exceptions.InvalidSchema, requests.exceptions.MissingSchema) as e:
        if modules.shared.is_connected_to_api:
            logging.warning(f"Malformed API server URL: {str(e)}")
            modules.shared.is_connected_to_api = False
        time.sleep(Config.API_FAILURE_DELAY)
        return Box()


def process_queue():
    logging.info("Worker online, ready to process jobs.")
    been_waiting = False
    while True:
        time.sleep(Config.API_POLLING_DELAY)
        if not (job := get_job()):
            if not been_waiting:
                logging.info(
                    f"Waiting for job from API queue '{Config.API_URL}'"
                )
                been_waiting = True
            update_status_message(status="idle", task="idle")

        job_failed = False
        job_start_time = datetime.now()
        been_waiting = False
        job_title = job.job_title
        job_id = job.job_id
        job_tasks = [list(i.keys())[0] for i in job.tasks]
        job_tasks_str = " -> ".join(job_tasks)
        update_status_message(
            status="in_progress",
            job_title=job_title,
            job_id=job_id,
            task="preparing",
        )
        logging.info(f"ACCEPTED JOB: {job_title}: {job_id}")
        logging.info(f" + [{job_title}] Tasks in job: {job_tasks_str}")
        for task_data in job.tasks:
            task = list(task_data.keys())[0]
            update_status_message(
                status="in_progress", job_title=job_title, job_id=job_id, task=task
            )
            data = task_data[task]
            task_start_time = datetime.now()
            module_path = f"modules.{task}"
            try:
                module = getattr(
                    importlib.import_module(module_path), task.capitalize()
                )
            except (AttributeError, ModuleNotFoundError):
                logging.critical(
                    f" ! [{job_title} -> {task}] TASK FAILED: Could not load module, abandoning task."
                )
                logging.critical(f"JOB FAILED: {job_title}: {job_id}")
                job_failed = True
                break
            try:
                task_instance = module(data=data, job_title=job_title)
            except JobModuleInitError as e:
                logging.critical(
                    f" ! [{job_title}] Could not initialize module '{task}': {e.message}"
                )
                logging.critical(f"JOB FAILED: {job_title}: {job_id}")
                job_failed = True
                break
            logging.info(f" + [{job_title}] Successfully loaded module: {task}")
            logging.debug(f" + [{job_title} -> {task}] Validating data: '{data}'")
            try:
                task_instance.validate()
                logging.info(
                    f" + [{job_title} -> {task}] Running task from module..."
                )
                task_instance.run()
            except (
                JobValidationError,
                JobRunFailureError,
                JobConfigurationError,
            ) as e:
                logging.critical(
                    f" ! [{job_title} -> {task}] {type(e).__name__}: {e.message}"
                )
                logging.critical(f"JOB FAILED: {job_title}: {job_id}")
                job_failed = True
                break
            task_run_time = datetime.now() - task_start_time
            logging.info(
                f" + [{job_title} -> {task}] Completed task in '{task_run_time}'."
            )
        if not job_failed:
            logging.info(f"COMPLETED JOB: {job_title}: {job_id}")
            job_run_time = datetime.now() - job_start_time
            logging.info(f"DURATION: {job_run_time}")


def graceful_exit(_sig, _frame):
    logging.info("Exiting the program due to SIGINT")
    sys.exit(1)


if __name__ == "__main__":
    main()
