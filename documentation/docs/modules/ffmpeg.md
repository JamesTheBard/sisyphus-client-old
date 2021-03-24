---
title: Ffmpeg Module
---

## Overview

The `ffmpeg` module data layout is based off the way `ffmpeg` lays out its command-line options.  While it doesn't seem intuitive, it does make sense when you start thinking about sources and output maps.

It does require that the Ffmpeg binary is installed on the worker, and that it is in the system path.  If it's not, the job will _definitely_ fail.

## Sources

The `sources` are simply that: input sources.  They will be labelled in the order they appear in the `sources` section.

## Source Maps

In the `source_maps` section, the `source` is the index of the source file in the `sources` section, the `stream_type` is the type of stream we want to map (`v` for video, `a` for audio, and `s` to subtitles), and the `stream` is the stream number of type `stream_type` in the source file.  For example, the second audio stream in the first source file would be:

```json title="Source Map Example"
{
  "source": 0,
  "stream_type": "a",
  "stream": 1
}
```

:::note

All sources and streams are zero-indexed, so the first one is `0`, the second one being `1`, and so on.

:::

## Output Maps

In the `output_maps` section, the sources are zero-indexed from the `source_maps` section.  The order of the source maps after they've been built are used here.  Also, the source maps are done via stream type meaning each are zero-indexed.

```json title="Output Map Example"
{
  "stream_type": "v",
  "stream": 1,
  "profile": "dark-and-stormy",
  "options": {
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

For the profile, the format that needs to be in the MongoDB is as follows.  The `settings` section literally gets placed into the output map `options` settings, then overriden by what was defined originally in the `options` section.

```json title="MongoDB Profile Example"
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

Profiles are loaded from MongoDB and contain a defined list of options and are pulled via its name.  Options can be defined outside of a profile, and if both are specified the `options` section overrides those contained in the profile.

## Output File

The `output_file` field is just where the final output file will be saved to.

## Full Example

```json title="Ffmpeg Data Format"
{
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
```