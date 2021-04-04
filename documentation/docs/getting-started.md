---
title: Getting Started
slug: /
---

The `sisyphus` worker is a flexible bit of Python that allows you to craft custom modules that are fed from a Redis queue and perform whatever you want them to.

## Requirements

Sisyphus currently requires:

- Redis server
- Python 3.8+
- Linux/UNIX operating system

:::note

There is no reason this won't work in Windows, it just has never been tested.  The default modules included with Sisyphus have really, _really_ never been tested with Windows so there's a significant chance they will not work.  However, if custom modules are built (or you find yourself as an enterprising person with respect to the current modules) with Windows in mind then there shouldn't be any reason the workers themselves won't run under Windows.

:::

It's also highly recommended that you use something to feed the Redis queue as it's the primary method that the workers send information for things like heartbeat and progress.  Sisyphus modules may have additional requirements to run, but the worker itself doesn't require anything more than this.

## Data Structure

The data structure is simple and detailed below.  The job information is stored in the Redis queue as a JSON string, and converted back to JSON by the Sisyphus worker.  While it's not the most imaginative method, it is very simple and very effective.

Each job is defined as a set of modules; this is because each task in a job is literally a Python module.  The data associated with each module will be specific to the module being used.  However, outside of those there is information that needs to be there.  The `job_title` is a human-readable bit of information that describes the job.  The `job_id` is _usually_ a UUID that ensures that jobs with the same title can still be differentiated.

:::note

The worker is fairly easy to customize, but the information structure below must be followed.  The `job_title` and `job_id` are expected values that the worker expects.

:::

```json title="Example Data Structure"
{
  "job_title": "job_title_01",
  "job_id": "1248a932-32d1-4b76-88bd-3dab8e9d3cbb",
  "tasks": [
    {
      "ffmpeg": {
        "module_settings": "look_at_module_doc_for_all_the_data"
      }
    },
    {
      "mkvmerge": {
        "module_settings": "also_in_the_docs"
      }
    }
  ] 
}
```

## Heartbeat

The current status of a worker is sent via the heartbeat message every worker sends out on a 5 second interval.  The key that each worker sends its heartbeat to is `worker:${worker_id}` and carries data in the following format:

```json title="Heartbeat Format Example (Idle)"
{
  "status": "idle",
  "hostname": "encode001"
}
```

There are two other options that get populated when a job is taken by a worker: `job_id` and `job_title`.  All of the options are described below and their possible values.

```json title="Heartbeat Format Example (Processing Job)"
{
  "status": "in_progress",
  "hostname": "encode001",
  "job_id": "1248a932-32d1-4b76-88bd-3dab8e9d3cbb",
  "job_title": "awesome_job_1"
}
```

  - `status`: This can be any of the following values:
    - `idle`: Currently not processing a job and is polling the queue for work
    - `startup`: The worker is starting up
    - `in_progress`: The worker is processing a job from the queue
  - `hostname`: The hostname of the worker
  - `job_id`: The job ID (UUID) of the job taken from the queue
  - `job_title`: The descriptive name of the job taken from the queue

