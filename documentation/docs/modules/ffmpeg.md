---
title: Ffmpeg Module
---

## Overview

The `ffmpeg` module data layout is based off the way `ffmpeg` lays out its command-line options.  While it doesn't seem intuitive, it does make sense when you start thinking about sources and output maps.

It does require that the Ffmpeg binary is installed on the worker, and that it is in the system path.  If it's not, the job will _definitely_ fail.

### Requirements

- `ffmpeg` installed on the worker node, and either be in the system path or the binary's path defined in the `FFMPEG_BIN_PATH` configuration variable.

## Config Options

The following options can be used to configure various aspects of the module via the `config.py` file.

- `FFMPEG_BIN_PATH`: When defined, will set the path to the Ffmpeg binary
- `FFMPEG_MONGO_DB`: The MongoDB database that holds the profiles
- `FFMPEG_MONGO_COLLECTION`: The collection that holds the profiles
- `FFMPEG_MONGO_URI`: Connection URI to pass to the Python MongoDB for the profiles

## Data Format

### Sources

The `sources` are simply that: input sources.  They will be labelled in the order they appear in the `sources` section.

```json title="Sources Example"
{
  "sources": [
    "/mnt/cool_source_file.mkv",
    "/mnt/cool_audio_source.ac3"
  ]
}
```

### Source Map

In the `source_map` section, the `source` is the index of the source file in the `sources` section, the `stream_type` is the type of stream we want to map (`v` for video, `a` for audio, and `s` to subtitles), and the `stream` is the stream number of type `stream_type` in the source file.  For example, the second audio stream in the first source file would be:

```json title="Source Map Example"
{
  "source_map": [
    {
      "source": 0,
      "stream_type": "v",
      "stream": 0
    },
    {
      "source": 0,
      "stream_type": "a",
      "stream": 1
    }
  ]
}
```

:::note

All sources and streams are zero-indexed, so the first one is `0`, the second one being `1`, and so on.

:::

### Output Map

In the `output_map` section, the sources are zero-indexed from the `source_map` section.  The order of the source maps after they've been built are used here.  Also, the source maps are done via stream type meaning each are zero-indexed.

```json title="Output Map Example"
{
  "output_map": [
    {
      "stream_type": "v",
      "stream": 0,
      "options": {
        "codec": "libx265",
        "crf": 19,
        "pix_fmt": "yuv420p10le",
      }
    },
    {
      "stream_type": "a",
      "stream": 0,
      "profile": "opus-128k"
    }
  ]
}
```

### Profiles

For the profile, the format that needs to be in the MongoDB is as follows.  The `settings` section literally gets placed into the output map `options` settings, then overriden by what was defined originally in the `options` section.

```json title="MongoDB Audio Profile Example"
{
  "name": "opus-128k",
  "settings": {
    "codec": "libopus",
    "b": "128k",
    "ac": 2,
    "vbr": "on",
    "compression_level": 10,
    "frame_duration": 60,
    "application": "audio"
  }
}
```

An example profile for the x265 codec would look like this:

```json title="MongoDB Video Profile Example
{
  "name": "dark-and-stormy",
  "settings": {
    "codec": "libx265",
    "crf": 19,
    "pix_fmt": "yuv420p10le",
    "preset": "slow",
    "x265-params": {
      "limit-sao": 1,
      "bframes": 8,
      "psy-rd": 1,
      "psy-rdoq": 2,
      "aq-mode": 3
    }
  }
}
```

Profiles are loaded from MongoDB and contain a defined list of options and are pulled via its name.  Options can be defined outside of a profile, and if both are specified the `options` section overrides those contained in the profile.

### Output File

The `output_file` field is just where the final output file will be saved to.

```json title="Output File Example"
{
  "output_file": "/mnt/awesome_ffmpeg_file.ext"
}
```

## Full Example

```json title="Ffmpeg Data Format"
{
  "ffmpeg": {
    "sources": [
      "source_file_1.mkv",
      "source_file_2.ac3"
    ],
    "source_maps": [
      {
        "source": 0,
        "stream_type": "v",
        "stream": 0
      },
      {
        "source": 1,
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
    "output_file": "/shared/output_file.mkv"
  }
}
```

## Validation

- Looks for the `ffmpeg` binary.
- Verifies that all of the source paths exist on the worker filesystem and are actual files.

## Progress

The module sends progress information to Redis under the `progress:${worker_id}` key.  The format is:

```json title="Progress Format"
{
  "current_frame": "1240",
  "total_frames": "34337",
  "percent_complete": "3.61"
}
```
