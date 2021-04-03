from box import Box
from pathlib import Path
from typing import List, Union
import shlex
import shutil
import box


class HandbrakeTrack:
    """
    Used to store audio and subtitle information.  Since they're fairly simple, you just need to pass the track number
    and the options associated with each.  For available options, look under the Audio Options and Subtitles Options
    in the help of HandBrakeCLI
    """

    track: Union[int, str]
    options: Box

    def __init__(self, track: Union[int, str], options: Union[Box, dict] = None):
        """
        HandbrakeTrack constructor
        :param track: The track from the source file
        :param options: The options for that track
        """
        self.track = track
        if options is not None:
            self.options = Box(options)
        else:
            self.options = Box()


class Handbrake:
    """
    The core Handbrake module. This will build a correct CLI set of arguments for the HandBrakeCLI binary.
    """

    __source: Path
    __output_file: Path
    cli_path: Path
    source_options: Box
    destination_options: Box
    video_options: Box
    audio_tracks: List[HandbrakeTrack]
    subtitle_tracks: List[HandbrakeTrack]

    def __init__(self, cli_path: Union[Path, str] = None):
        """
        Handbrake constructor
        :param cli_path: Override the HandBrakeCLI binary path
        """
        if cli_path:
            self.cli_path = Path(cli_path)
        else:
            self.cli_path = Path(shutil.which('HandBrakeCLI'))
        self.video_options = Box()
        self.source_options = Box()
        self.destination_options = Box()
        self.encoder_options = Box()
        self.picture_options = Box()
        self.filters_options = Box()
        self.subtitle_tracks = list()
        self.audio_tracks = list()

    @property
    def source(self) -> Path:
        """
        Return the source file as a Path
        :return: Path of the source file
        """
        return Path(self.__source)

    @source.setter
    def source(self, source_file: Union[str, Path]):
        """
        Sets the source file path and ensures it's an actual Path object
        :param source_file: The path of the source file (either string or Path)
        """
        self.__source = Path(source_file)

    @property
    def output_file(self) -> Path:
        """
        Return the output file as a Path
        :return: Path of the output file
        """
        return Path(self.__output_file)

    @output_file.setter
    def output_file(self, output_file: Union[str, Path]):
        """
        Sets the output file path and ensures it's an actual Path object
        :param output_file:
        """
        self.__output_file = Path(output_file)

    @staticmethod
    def __generate_generic_options(source: Box) -> List[str]:
        """
        Converts a Box of key/value options into a list of command-line parameters that can be used to feed
        HandBrake.  Keys should avoid using dashes and instead use underscores which will be converted into dashes
        for the key values.
        :param source: Box of key/value options
        :return: List of processed command-line options
        """
        command = list()
        for k, v in source.items():
            key = str(k).replace('_', '-')
            if len(k) == 1:
                command.append(f'-{key}')
            else:
                command.append(f'--{key}')
            if v is not None and type(v) is not bool:
                command.append(v)
        return [str(i) for i in command]

    def generate_video_options(self) -> List[str]:
        """
        Generates the video options.
        :return: List of video options for the CLI
        """
        return self.__generate_generic_options(self.video_options)

    def generate_source_options(self) -> List[str]:
        """
        Generates the source options.
        :return: List of source options for the CLI
        """
        command = ['-i', str(self.source.absolute())]
        command.extend(self.__generate_generic_options(self.source_options))
        return command

    def generate_destination_options(self) -> List[str]:
        """
        Generates the destination options.
        :return: List of source options for the CLI
        """
        command = ['-o', str(self.output_file.absolute())]
        command.extend(self.__generate_generic_options(self.destination_options))
        return command

    def generate_filters_options(self) -> List[str]:
        """
        Generates the filters options.
        :return: List of filters options for the CLI
        """
        return self.__generate_generic_options(self.filters_options)

    def generate_picture_options(self) -> List[str]:
        """
        Generates the picture options.
        :return: List of picture options for the CLI
        """
        return self.__generate_generic_options(source=self.picture_options)

    def generate_track_options(self, track_type: str) -> List[str]:
        """
        Processes all of the tracks in a list, then merges them into the appropriate CLI values (used for audio and
        subtitles)
        :param track_type: Type of track (either 'audio' or 'subtitles')
        :return: List of audio/subtitle options for the CLI
        """
        unset_value = '-1'
        options_list = list()
        tracks = getattr(self, f'{track_type}_tracks')
        if len(tracks) == 0:
            return list()
        for t in tracks:
            [options_list.append(k) for k in t.options.keys() if k not in options_list]

        results = Box()
        for option in options_list:
            results[option] = list()
        results[track_type] = [str(i.track) for i in tracks]
        for t in tracks:
            for option in options_list:
                try:
                    results[option].append(t.options[option])
                except box.exceptions.BoxKeyError:
                    results[option].append(unset_value)
        results = {k: ','.join(v) for k, v in results.items()}
        return self.__generate_generic_options(Box(results))

    def generate_audio_options(self) -> List[str]:
        """
        Generates the appropriate audio options from the tracks provided
        :return: List of audio options for the CLI
        """
        return self.generate_track_options(track_type="audio")

    def generate_subtitle_options(self) -> List[str]:
        """
        Generates the appropriate subtitle options from the tracks provided
        :return: List of subtitle options for the CLI
        """
        return self.generate_track_options(track_type="subtitle")

    def generate_cli(self, to_string: bool = False) -> Union[str, List]:
        """
        Generates the full command-line parameter set including the HandBrake binary path.
        :param to_string: Convert the HandBrakeCLI command to a string
        :return: Return the HandBrakeCLI command options
        """
        option_list = [
            self.generate_source_options,
            self.generate_video_options,
            self.generate_picture_options,
            self.generate_audio_options,
            self.generate_subtitle_options,
            self.generate_destination_options,
            self.generate_filters_options,
        ]
        command = [str(self.cli_path)]
        [command.extend(i()) for i in option_list]
        if to_string:
            return shlex.join(command)
        return command


if __name__ == "__main__":
    """
    This is a quick example of how everything works.  If adding options that require dashes, they need to be replaced
    with underscores.  Also, beginning dashes for options should be removed. 
    
    For example: --no-deinterlace -> "no_deinterlace"
    
    Tracks don't require options, and you don't have to ensure that every track has all of the options defined for each
    track added.  Handbrake will figure all that out on its own. 
    
    Options that have no associated values (e.g. flags) must have a value associated with them of either None or True.
    This will tell Handbrake to drop the value from the parameter list.
    
    Source file and output files need to be defined _outside_ of their option groups.  This makes it easier to
    validate.
    """
    h = Handbrake()
    h.source = "test 2.mkv"
    h.output_file = "output.mkv"
    h.video_options.encoder = "x265_10bit"
    h.video_options.q = 19
    h.source_options.chapters = "1-3"
    h.audio_tracks.append(HandbrakeTrack(track=1, options={"aencoder": "opus", "downmix": "stereo", "ab": "128"}))
    h.audio_tracks.append(HandbrakeTrack(track=2, options={"aencoder": "ac3"}))
    h.subtitle_tracks.append(HandbrakeTrack(track=1))
    h.subtitle_tracks.append(HandbrakeTrack(track=2))
    h.filters_options.no_comb_detect = True
    h.filters_options.no_deinterlace = True
    h.picture_options.w = 1920
    h.picture_options.h = 1080
    h.destination_options.format = "av_mkv"
    print(h.generate_cli(to_string=True))
