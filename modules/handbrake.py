import os
import re
import subprocess
import time
from pathlib import Path
from modules.base import BaseModule
from modules.exceptions import JobValidationError, JobRunFailureError
from helpers.handbrake import Handbrake as Hb
from helpers.handbrake import HandbrakeTrack
from helpers.ffmpeg import FfmpegInfo


class Handbrake(BaseModule):

    def __init__(self, data: dict, job_title: str):
        super().__init__(data, job_title)
        self.module_name = 'handbrake'
        self.encoder = Hb()
        self.encoder.cli_path = Path(os.getenv('HANDBRAKE_CLI_PATH', self.encoder.cli_path))

    def process_data(self):
        self.encoder.source = self.data.source
        self.encoder.output_file = self.data.output_file

        # Go through each group and put the data where Hanbrake expects it to be.  If it's not there, no big deal,
        # just skip it as the default for the module is an empty Box.
        option_sections = [
            "general",
            "source",
            "destination",
            "video",
            "picture",
            "filters",
        ]
        for option in option_sections:
            try:
                setattr(self.encoder, f'{option}_options', self.data[f'{option}_options'])
            except KeyError:
                pass

        # Need to add all the tracks to the audio and subtitle sections.  Again, if there are no audio or subtitle
        # tracks associated with it, then it's not an issue.
        track_sections = [
            "audio",
            "subtitle",
        ]
        for section in track_sections:
            try:
                for track in self.data[f'{section}_tracks']:
                    a = getattr(self.encoder, f'{section}_tracks')
                    a.append(HandbrakeTrack(**track))
            except TypeError:
                raise JobValidationError(
                    message=f'Only "track" and "option" definitions allowed in {section} track!',
                    module=self.module_name
                )
            except KeyError:
                pass

    def run(self):
        self.process_data()
        total_frames = FfmpegInfo(source_file=self.encoder.source).video_tracks[0].frames
        command = self.encoder.generate_cli()
        if "--json" not in command:
            command.append('--json')
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while True:
            time.sleep(1)
            if (return_code := process.poll()) is not None:
                break
            for line in process.stdout:
                if match := re.search(r'"Progress": (\d+\.\d+)', line.decode()):
                    completed_perc = float(match.group(1))
                    progress = {
                        "current_frame": int(completed_perc * total_frames),
                        "total_frames": total_frames,
                        "percent_complete": '{:0.2f}'.format(completed_perc * 100),
                    }
                    self.update_progress(progress)

        if return_code != 0:
            raise JobRunFailureError(
                message=f"'{self.module_name}' returned exit code {return_code}",
                module=self.module_name
            )
        return True

    def validate(self):
        if not self.encoder.cli_path.exists():
            raise JobValidationError(
                message=f"Could not find the HandBrake CLI binary at '{self.encoder.cli_path.absolute()}'",
                module=self.module_name
            )
        if 'source' not in self.data.keys():
            raise JobValidationError(
                message="No source file specified.",
                module=self.module_name
            )
        if not Path(self.data.source).exists() or not Path(self.data.source).is_file():
            raise JobValidationError(
                message=f"The source file '{Path(self.data.source).absolute()}' either does not exist "
                        f"or is not a file.",
                module=self.module_name
            )
