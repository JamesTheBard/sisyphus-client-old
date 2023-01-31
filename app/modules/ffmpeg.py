import json
import logging
import os
import re
import shlex
import subprocess
import time
from pathlib import Path
from urllib.parse import urljoin

import box
import requests

from config import Config
from helpers.ffmpeg import Ffmpeg as Ff
from helpers.ffmpeg import FfmpegInfo, Source, SourceOutput
from modules import exceptions as ex
from modules.base import BaseModule


class Ffmpeg(BaseModule):
    def __init__(self, data: dict, job_title: str):
        super().__init__(data, job_title)
        self.encoder = Ff()
        self.encoder.ffmpeg_path = os.getenv("FFMPEG_PATH", self.encoder.ffmpeg_path)
        self.module_name = "ffmpeg"

    def process_files(self):
        self.encoder.output = self.data.output_file
        self.encoder.inputs.extend(self.data.sources)
        self.encoder.settings.overwrite = True

        self.build_source_map()
        self.build_source_outputs()

    def validate(self):
        self.process_files()
        if not self.encoder.ffmpeg_path:
            raise ex.JobValidationError(
                message=f"Could not find the Ffmpeg binary.", module="ffmpeg"
            )

        for file in [Path(i) for i in self.encoder.inputs]:
            if not file.is_file() or not file.exists():
                raise ex.JobValidationError(
                    message=f"Input file '{file.name}' does not exist.", module="ffmpeg"
                )

    def run(self):
        video_info = FfmpegInfo(Path(self.data.sources[0]))
        total_frames = video_info.video_tracks[0].frames

        command_raw = self.encoder.generate_command()
        logging.info(f" + [ffmpeg] Full command: {command_raw}")
        command = shlex.split(command_raw)
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )

        while True:
            time.sleep(1)
            if (return_code := process.poll()) is not None:
                break
            for line in process.stdout:
                if match := re.search(r"frame=(\s*\d+)", line.decode()):
                    current_frame = int(match.group(1))
                    progress = {
                        "current_frame": current_frame,
                        "total_frames": total_frames,
                        "percent_complete": "{:0.2f}".format(
                            current_frame / total_frames * 100
                        ),
                    }
                    self.update_progress(progress)

        if return_code != 0:
            raise ex.JobRunFailureError(
                message=f"`ffmpeg` command returned exit code {return_code}",
                module="ffmpeg",
            )
        return True

    def build_source_map(self):
        for source in self.data.source_map:
            temp = Source(
                source=source.source,
                stream_type=source.stream_type,
                stream=source.stream,
            )
            self.encoder.mapped_sources.append(temp)

    def build_source_outputs(self):
        for output in self.data.output_map:
            encode_options = dict()

            try:
                encode_payload = {
                    "module": "ffmpeg",
                    "dataset": "profiles",
                    "name": output.profile,
                }
                encode_profile = json.loads(
                    requests.get(
                        urljoin(Config.API_URL, "/worker/data"), params=encode_payload
                    ).text
                )
                encode_profile_options = encode_profile["settings"]
                encode_options.update(encode_profile_options)
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.InvalidSchema,
                requests.exceptions.MissingSchema,
                requests.exceptions.InvalidURL,
            ):
                raise ex.JobValidationError(
                    message=f"The profile '{output.profile}' was not found, abandoning job.",
                    module=self.module_name,
                )
            except box.exceptions.BoxKeyError:
                pass
            except IndexError:
                raise ex.JobValidationError(
                    message=f"The profile '{output.profile}' was not found, abandoning job.",
                    module=self.module_name,
                )
            try:
                encode_options.update(output.options)
            except box.exceptions.BoxKeyError:
                pass

            temp = SourceOutput(
                stream_type=output.stream_type,
                stream=output.stream,
                options=encode_options,
            )
            self.encoder.mapped_outputs.append(temp)
