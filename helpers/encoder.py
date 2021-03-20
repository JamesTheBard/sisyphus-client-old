from pymediainfo import MediaInfo, Track
from pathlib import Path
from typing import Union
from box import Box
import json


class JobEncoder:

    content: Box
    job: str

    def __init__(self, job: Union[bytes, str]):
        if type(job) is bytes:
            job = job.decode()
        self.job = job
        self.content = self.parse_json(job)
        self.verify_source_files()

    @staticmethod
    def parse_json(content: str) -> Box:
        return Box(json.loads(content))

    def verify_source_files(self):
        files = list()
        files.append(self.content.source_config.video.file)
        for i in self.content.source_config.audio:
            files.append(i.file)
        for i in self.content.source_config.subtitles:
            files.append(i.file)
        files = [Path(i) for i in files]
        for f in files:
            if not f.is_file():
                raise FileNotFoundError("Could not find " + str(f))

    @staticmethod
    def get_track_information(source_file: Union[Path, str], track: int = 0) -> Track:
        """
        Get track information from a media file
        :param source_file: The media file path
        :param track: The track number
        :return: Track information from the file
        """
        source_file = Path(source_file)
        info = MediaInfo.parse(source_file)
        return [i for i in info.tracks if i == track][0]

