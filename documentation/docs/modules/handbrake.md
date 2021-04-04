---
title: Handbrake Module
---

## Overview

The `Handbrake` module is the Swiss Army knife of encoders, and can tackle some problems that `ffmpeg` may have some issues with.  The options layout is very, very similar to that of the `HandBrakeCLI` options.

It does require that the Handbrake binary is installed on the worker, and that it is in the system path.  If it's not, the job will _definitely_ fail.

### Requirements

- `HandBrakeCLI` installed on the worker node, and either be in the system path or the binary's path defined in the `HANDBRAKE_CLI_PATH` configuration variable.

## Config Options

The following options can be used to configure various aspects of the module via the `config.py` file.

- `HANDBRAKE_CLI_PATH`: When defined, will set the path to the `HandBrakeCLI` binary

## Data Format

Options are added to a given section, and those are converted to `HandBrakeCLI` options.  You do not need to add the preceeding dashes to the options, the module will handle all of that.  Also, options can use either dashes or underscores.  For example, `no-deinterlace` and `no_deinterlace` both get converted to `--no-deinterlace` for the command-line option.

Also, for flagged options (like `no_deinterlace`), you still need to provide a value for the option.  The value can be either `true` or `null` and it will just add the flag to the command line arguments.

:::info

If you have a section with no options then you don't have to define it.  For example, if there are no general options, then you do not need to define a `general_options` section.

:::


### Source

The `source` is the file that Handbrake will be processing.  You can only specify one source.

```json title="Source Example"
{
  "source": "/mnt/cool_source_file.mkv"
}
```

### Output File

The `output_file` specifies where Handbrake is going to save the resulting file after processing the input.

```json title="Output File Example"
{
  "output_file": "/mnt/output_file.mkv"
}
```

### Option Sections

For any of the options listed in the `HandBrakeCLI` documentation, all of them can be used in their associated option section.  If you have any doubts about what goes where, just run the `HandBrakeCLI` binary with the `--help` option and it should give you a ton of options in various sections.

#### General Options

General options live in the `general_options` section.  This includes things like `json` progress output and not much else.

```json title="General Options Example"
{
  "general_options": {
    "json": true
  }
}
```

:::info

The `json` option is always added to the command so that the module can track the progress of the encode.  However, there aren't really that many great options to show how this section works as an example, and this section will usually be left out of the JSON fed to the worker.

:::

#### Source Options

Source options allow you to specify parts of a source file to process.  The only option that should not be set here is the `input` option as this needs to be set via the `source` key mentioned earlier.  Setting it here as well could cause things to behave really, really badly or explode.

```json title="Source Options Example"
{
  "source_options": {
    "chapters": "1-5"
  }
}
```

:::warning

Again, do not set the `input` option in _any_ options location.  You will make the module very, very sad.

:::

#### Destination Options

This section holds all of the destination file options for Handbrake.  Do not use the `output` option here; the `output_file` setting must be used to tell the module where it should save the processed file at.

```json title="Destination Options Example"
{
  "destination_options": {
    "format": "av_mkv"
  }
}
```

:::warning

Do not set the `output` setting in any options section.  This will also make the module sad.  You can set any other options except for that one.

:::

#### Video Options

All video options are set in this section.  Pretty straightforward.

```json title="Video Options Example"
{
  "video_options": {
    "encoder": "x264",
    "q": 22,
    "encoder_preset": "slow"
  }
}
```

#### Picture Options

Picture options like cropping, pixel aspect ratio, and color matricies are contained here.

```json title="Picture Options Example"
{
  "picture_options": {
    "width": 1920,
    "height": 1080
  }
}
```

#### Filters Options

Filters such as deinterlacing, decombing, detelicine go here.

```json title="Filters Options Example"
{
  "filters_options": {
    "no_comb_detect": true,
    "chroma_smooth_tune": "small",
    "grayscale": true
  }
}
```

### Audio and Subtitle Tracks

The `handbrake` module will automatically generate the combined parameters that Handbrake uses for audio and subtitle tracks.  Each track has to be defined separately, and is fairly easy.

```json title="Audio Tracks Example"
{
  "audio_tracks": [
    {
      "track": 1,
      "aencoder": "opus",
      "6": "stereo",
      "ab": 128
    },
    {
      "track": 2,
      "aencoder": "ac3",
      "drc": 1.5
    }
  ]
}
```

```json title="Subtitle Tracks Example"
{
  "subtitle_tracks": [
    {
      "track": 1
    },
    {
      "track": 2
    }
  ]
}
```

:::info

There really aren't a lot of subtitle options that are used, but they can be added in the same way the options are in the audio tracks section.

:::

## Full Example

```json title="Full Example"
{
  "handbrake": {
    "source": "/mnt/source_file.mkv",
    "output_file": "/mnt/output_file.mkv",
    "general_options": {
      "json": true
    },
    "source_options": {
      "chapters": "1-5"
    },
    "destination_options": {
      "format": "av_mkv"
    },
    "video_options": {
      "encoder": "x264",
      "q": 22,
      "encoder_preset": "slow"
    },
    "picture_options": {
      "w": 1920,
      "h": 1080
    },
    "filters_options": {
      "chroma_smooth_tune": "tiny"
    },
    "audio_tracks": [
      {
        "track": 1,
        "aencoder": "opus",
        "6": "stereo",
        "ab": 128
      },
      {
        "track": 2,
        "aencoder": "ac3",
        "drc": 1.5
      }
    ],
    "subtitle_tracks": [
      {
        "track": 1
      },
      {
        "track": 2
      }
    ]
  }
}
```

:::info

Dirty secret: all options can be lumped into the same section.  The multitude of sections are there to make organizing their options a bit easier on the eyes.  This does not apply to the `audio_tracks` and `subtitle_tracks` sections!

:::

## Validation

- Looks for the `HandBrakeCLI` binary.
- Verifies that the `source` and `output_file` options are defined in the data.
- Verifies that the source exists on the worker filesystem and is an actual file.