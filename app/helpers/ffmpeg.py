import re
import shlex
import shutil
import subprocess
import time
from pathlib import Path
from typing import List, NamedTuple, Union

from pymediainfo import MediaInfo
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

SUBTITLES = "s"
AUDIO = "a"
VIDEO = "v"


class TrackInfo(NamedTuple):
    codec: str
    track: int
    language: str
    bitrate: str
    forced: bool
    default: bool
    frames: int
    type: str
    title: str = None
    channels: str = None


class Source:
    source: int
    stream_type: str
    stream: int

    def __init__(
        self, source: int, stream_type: str = None, stream: int = None
    ) -> None:
        self.source = source
        self.stream_type = stream_type
        self.stream = stream

    @property
    def cli_options(self):
        o = f"{self.source}"
        if self.stream_type is not None:
            o += f":{self.stream_type}"
        if self.stream is not None:
            o += f":{self.stream}"
        return f"-map {o}"


class SourceOutput:
    stream_type: str
    stream: int
    options: dict

    def __init__(
        self, stream_type: str = None, stream: int = None, options: dict = None
    ):
        self.stream_type = stream_type
        self.stream = stream
        if options:
            self.options = options
        else:
            self.options = dict()

    @property
    def cli_options(self):
        command = ""
        template = list()
        if self.stream_type is not None:
            template.append(f"{self.stream_type}")
        if self.stream is not None:
            template.append(f"{self.stream}")
        template = ":".join(template)
        for k, v in self.options.items():
            if template:
                has_template = ":"
            else:
                has_template = ""
            if type(v) is dict:
                i = ":".join([f"{i}={j}" for i, j in v.items()])
                command += f"-{k}{has_template}{template} {i} "
            else:
                command += f"-{k}{has_template}{template} {v} "
        return command.strip()


class FfmpegMiscSettings:

    overwrite: bool
    progress_bar: bool
    video_info: TrackInfo

    def __init__(self):
        self.overwrite = False
        self.progress_bar = False
        self.video_info = None


class Ffmpeg:

    inputs: List[Path]
    mapped_sources: List[Source]
    __output: Union[str, Path]
    source_outputs: List[SourceOutput]
    settings: FfmpegMiscSettings

    def __init__(self, ffmpeg_path: Path = None):
        if ffmpeg_path:
            self.ffmpeg_path = Path(ffmpeg_path)
        else:
            self.ffmpeg_path = Path(shutil.which("ffmpeg"))
        self.inputs = list()
        self.mapped_sources = list()
        self.mapped_outputs = list()
        self.settings = FfmpegMiscSettings()

    def generate_command(self) -> str:
        command = f"{self.ffmpeg_path} "
        if self.settings.overwrite:
            command += "-y "
        command += "-progress pipe:1 "
        for i in self.inputs:
            command += f'-i "{i}" '
        for source in self.mapped_sources:
            command += f"{source.cli_options} "
        for source_output in self.mapped_outputs:
            command += f"{source_output.cli_options} "
        command += f'"{self.output}"'
        return command.strip()

    def run(self, verbose: bool = False) -> None:
        command = shlex.split(self.generate_command())
        if verbose:
            subprocess.run(command)
        else:
            frames = self.settings.video_info.frames
            progress = Progress(
                TextColumn("[#ffff00]»[bold green] encode"),
                BarColumn(
                    bar_width=None,
                ),
                "[progress.percentage]{task.percentage:>3.1f}%",
                "•",
                "[green]{task.completed}/{task.total}[/green]",
                "•",
                TimeRemainingColumn(),
            )
            progress.start()
            task = progress.add_task("test")
            progress.update(task, total=frames)
            process = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )

            regex = r"frame=(\s*\d+)"
            while True:
                time.sleep(0.05)
                output = process.stdout.readline()
                if process.poll() is not None:
                    break
                if output:
                    if m := re.search(regex, output.decode()):
                        progress.update(task, completed=int(m.group(1)))
            progress.update(task, completed=frames)
            progress.stop()

    @property
    def output(self) -> Path:
        return self.__output

    @output.setter
    def output(self, path: Union[str, Path]) -> None:
        self.__output = Path(path)


class FfmpegInfo:
    def __init__(self, source_file: Path):
        self.source_file = source_file
        self.data = MediaInfo.parse(self.source_file)

    @property
    def video_tracks(self):
        return self.process_tracks("Video")

    @property
    def audio_tracks(self):
        return self.process_tracks("Audio")

    @property
    def subtitle_tracks(self):
        return self.process_tracks("Text")

    @property
    def tracks(self):
        return self.process_tracks("All")

    def process_tracks(self, category: str):
        if category != "All":
            info = [i for i in self.data.tracks if i.track_type == category]
        else:
            info = self.data.tracks
        temp = list()
        count = 0
        for t in info:
            is_forced = False
            is_default = False
            if t.forced == "Yes":
                is_forced = True
            if t.default == "Yes":
                is_default = True
            temp.append(
                TrackInfo(
                    codec=t.codec_id,
                    track=count,
                    language=t.language,
                    bitrate=t.bit_rate,
                    channels=t.channel_s,
                    forced=is_forced,
                    default=is_default,
                    title=t.title,
                    frames=int(t.frame_count) if t.frame_count else None,
                    type=t.track_type,
                )
            )
            count += 1
        return temp

    @property
    def video_tracks_raw(self):
        return [i for i in self.data.tracks if i.track_type == "Video"]

    @property
    def audio_tracks_raw(self):
        return [i for i in self.data.tracks if i.track_type == "Audio"]

    @property
    def subtitle_tracks_raw(self):
        return [i for i in self.data.tracks if i.track_type == "Text"]
