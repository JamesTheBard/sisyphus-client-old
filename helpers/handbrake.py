from box import Box, BoxList
from pathlib import Path
from typing import List, Union
import shlex
import shutil
import box


class HandbrakeAudio:

    audio_track: Union[int, str]
    options: Box

    def __init__(self, audio_track: Union[int, str], options: Union[Box, dict]):
        self.audio_track = audio_track
        self.options = Box(options)


class HandbrakeSubtitle:

    subtitle_track: Union[int, str]
    options: Box

    def __init__(self, subtitle_track: Union[int, str], options: Union[Box, dict]):
        self.subtitle_track = subtitle_track
        self.options = Box(options)


class Handbrake:

    _source: Path
    _output_file: Path
    cli_path: Path
    source_options: Box
    destination_options: Box
    video_options: Box
    audio_tracks: List[HandbrakeAudio]
    subtitle_tracks: List[HandbrakeSubtitle]

    def __init__(self, cli_path: Union[Path, str] = None):
        if cli_path:
            self.cli_path = Path(cli_path)
        else:
            self.cli_path = Path(shutil.which('HandBrakeCLI'))
        self.video_options = Box()
        self.source_options = Box()
        self.destination_options = Box()
        self.encoder_options = Box()
        self.picture_options = Box()
        self.subtitle_tracks = list()
        self.audio_tracks = list()

    @property
    def source(self):
        return Path(self._source)

    @source.setter
    def source(self, source_file):
        self._source = Path(source_file)

    @property
    def output_file(self):
        return Path(self._output_file)

    @output_file.setter
    def output_file(self, output_file):
        self._output_file = Path(output_file)

    @staticmethod
    def __generate_generic_options(source: Box) -> List[str]:
        command = list()
        for k, v in source.items():
            if len(k) == 1:
                command.append(f'-{k}')
            else:
                command.append(f'--{k}')
            if v is not None:
                command.append(v)
        return [str(i) for i in command]

    def generate_video_options(self):
        return self.__generate_generic_options(self.video_options)

    def generate_source_options(self):
        command = ['-i', str(self.source.absolute())]
        command.extend(self.__generate_generic_options(self.source_options))
        return command

    def generate_track_options(self, track_type: str):
        options_list = BoxList()
        tracks = getattr(self, f'{track_type}_tracks')
        for track in tracks:
            [options_list.append(k) for k, _ in track.options.items() if k not in options_list]

        results = Box()
        for option in options_list:
            results[option] = list()
        results.audio = [str(i.audio_track) for i in self.audio_tracks]
        for track in tracks:
            for option in options_list:
                try:
                    results[option].append(track.options[option])
                except box.exceptions.BoxKeyError:
                    results[option].append('-1')
        results = {k: ','.join(v) for k, v in results.items()}
        return self.__generate_generic_options(results)

    def generate_audio_options(self):
        return self.generate_track_options(track_type="audio")

    def generate_subtitle_options(self):
        return self.generate_track_options(track_type="subtitle")

    def generate_cli(self, to_string: bool = False) -> Union[str, List]:
        option_list = [
            self.generate_source_options,
            self.generate_video_options,
            self.generate_audio_options,
            self.generate_subtitle_options,
        ]
        command = list()
        [command.extend(i()) for i in option_list]
        if to_string:
            return shlex.join(command)
        return command


if __name__ == "__main__":
    h = Handbrake()
    h.source = "test 2.mkv"
    h.video_options.encoder = "x265_10bit"
    h.video_options.q = 19
    h.source_options.chapters = "1-3"
    print(h.generate_cli(to_string=False))
    print(h.cli_path)

    h.audio_tracks.append(HandbrakeAudio(audio_track=1, options={"encoder": "opus", "downmix": "stereo", "ab": "128"}))
    h.audio_tracks.append(HandbrakeAudio(audio_track=2, options={"encoder": "ac3"}))
    print(h.generate_audio_options())
