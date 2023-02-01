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

## Installation

Installation is pretty easy: clone the repository, create a virtual environment, install the requirements, and then go.

```console
$ git clone git@gitlab.com:jamesthebard/sisyphus.git
$ cd sisyphus
$ python3 -m venv venv
$ source venv/bin/activate
$ pip install -r requirements
$ export REDIS_HOST=redis.host
$ python sisyphus.py
```

A quick-and-dirty Redis/Mongo `docker-compose` file to help with getting everything setup.  This includes MongoDB which is very useful with respect to the `ffmpeg` module.

```yaml
version: "3.3"

services:
  redis:
    image: eqalpha/keydb:latest 
    ports:
      - 6379:6379
    volumes:
      - /opt/lib/redis:/data
    entrypoint: "keydb-server /etc/keydb/keydb.conf --appendonly yes --server-threads 4"
  mongo:
    image: mongo:latest
    ports:
      - 27017:27017
    volumes:
      - /opt/lib/mongo:/data/db
    environment:
      MONGO_INITDB_ROOT_USERNAME: root
      MONGO_INITDB_ROOT_PASSWORD: root
  mongo-express:
    image: mongo-express:latest
    ports:
      - 8081:8081
    environment:
      ME_CONFIG_MONGODB_ADMINUSERNAME: root
      ME_CONFIG_MONGODB_ADMINPASSWORD: root
```

:::note

Sisyphus is usually paired with the `encoding-server` repository (`git@gitlab.com:jamesthebard/encoding-server.git`).  This is just a simple Flask application that puts things on the queue, grabs worker status, grabs queue status, and allows you to clear the queue all via API calls.  It also handles adding the `job_id` to jobs in the queue.

:::

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

## Full Example

```json title="Full Example of Job"
{
  "job_title": "encode_job_name",
  "tasks": [
    {
      "ffmpeg": {
        "sources": [
          "/mnt/phoenix/Videos/Streams/raw_test_video.mkv"
        ],
        "source_map": [
          {
            "source": 0,
            "stream_type": "v",
            "stream": 0
          },
          {
            "source": 0,
            "stream_type": "a",
            "stream": 0
          },
          {
            "source": 0,
            "stream_type": "s",
            "stream": 0
          }
        ],
        "output_map": [
          {
            "stream_type": "v",
            "stream": 0,
            "profile": "dark-and-stormy"
          },
          {
            "stream_type": "a",
            "stream": 0,
            "profile": "opus-128k"
          },
          {
            "stream_type": "s",
            "stream": 0,
            "options": {
              "codec": "copy"
            }
          }
        ],
        "output_file": "/mnt/phoenix/Videos/Streams/temp.mkv"
      }
    },
    {
      "mkvmerge": {
        "sources": [
          "/mnt/phoenix/Videos/Streams/output_file.mkv"
        ],
        "tracks": [
          {
            "source": 0,
            "track": 0,
            "options": {
              "language": "und",
              "default-track": "yes",
              "title": "Awesome Newly Muxed Video"
            }
          },
          {
            "source": 0,
            "track": 1,
            "options": {
              "language": "jpn",
              "default-track": "yes"
            }
          },
          {
            "source": 1,
            "track": 0,
            "options": {
              "language": "eng",
              "default-track": "yes",
              "track-title": "Full Subtitles"
            }
          }
        ],
        "output_file": "/mnt/phoenix/Videos/Streams/awesome_newly_muxed_video.mkv",
        "options": {
          "no-global-tags": null,
          "no-track-tags": null,
          "title": "Awesome Newly Muxed Video"
        }
      }
    },
    {
      "cleanup": {
        "verify_exists": [
          "/mnt/phoenix/Videos/Streams/awesome_newly_muxed_video.mkv"
        ],
        "delete_files": [
          "/mnt/phoenix/Videos/Streams/temp.mkv"
        ]
      }
    }
  ]
}
```