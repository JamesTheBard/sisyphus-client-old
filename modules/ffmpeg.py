import re
import shlex
import subprocess
import time
from pathlib import Path
from pymongo import MongoClient

from config import Config
from helpers.ffmpeg import Ffmpeg as Ff
from helpers.ffmpeg import FfmpegInfo, Source, SourceOutput
from modules import exceptions as ex
from modules.base import BaseModule


class Ffmpeg(BaseModule):

    def __init__(self, data: dict, job_title: str):
        super().__init__(data, job_title)
        self.encoder = Ff()
        self.mongo = MongoClient(Config.MONGO_URI)
        self.process_files()

    def process_files(self):
        self.encoder.output = self.data.output_file
        self.encoder.inputs.extend(self.data.sources)
        self.encoder.settings.overwrite = True

        self.build_source_map()
        self.build_source_outputs()

    def validate(self):
        if not self.encoder.ffmpeg_path:
            raise ex.JobValidationError(message=f"Could not find the Ffmpeg binary.", module='ffmpeg')

        for file in self.encoder.inputs:
            if not file.is_file() or not file.exists():
                raise ex.JobValidationError(message=f"Input file '{file.name}' does not exist.", module='ffmpeg')

    def run(self):
        video_info = FfmpegInfo(Path(self.data.sources[0]))
        total_frames = video_info.video_tracks[0].frames

        command = shlex.split(self.encoder.generate_command())
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        while True:
            time.sleep(1)
            if return_code := process.poll():
                break
            for line in process.stdout:
                if match := re.search(r'frame=(\s*\d+)', line.decode()):
                    current_frame = int(match.group(1))
                    progress = {
                        "current_frame": current_frame,
                        "total_frames": total_frames,
                        "percent_complete": '{:0.2f}'.format(current_frame / total_frames * 100),
                    }
                    self.update_progress(progress)

        if return_code != 0:
            raise ex.JobRunFailureError(message=f"`ffmpeg` command returned exit code {return_code}", module="ffmpeg")
        return True

    def build_source_map(self):
        for source in self.data.source_map:
            temp = Source(
                source=source.source,
                stream_type=source.stream_type,
                stream=source.stream
            )
            self.encoder.mapped_sources.append(temp)

    def build_source_outputs(self):
        for output in self.data.output_map:
            encode_options = self.mongo.get_database(Config.MONGO_DB) \
                .get_collection(Config.MONGO_COLLECTION_PROFILES) \
                .find({'name': output.profile})
            encode_options = list(encode_options)[0]
            temp = SourceOutput(
                stream_type=output.stream_type,
                stream=output.stream,
                options=encode_options['settings']
            )
            self.encoder.mapped_outputs.append(temp)
