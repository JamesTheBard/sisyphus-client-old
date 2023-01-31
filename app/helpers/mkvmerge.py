import json
import shlex
import shutil
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List, Union

from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

__all__ = [
    "Matroska",
    "MkvSource",
    "MkvSourceTrack",
    "MkvAttachment",
]


class MkvSourceTrack:
    """
    An object to associate tracks with MkvSources
    """

    options: dict
    track: int

    def __init__(self, track: int) -> None:
        """
        Create an MkvSourceTrack object.  This is used to pull a given track from a source.
        :param track: The track to use of a given source.
        """
        self.track = track
        self.options = dict()

    def set_option(self, option: str, value: str = None) -> None:
        """
        Set an option for the track.
        :param option: The option name (not including the double dashes)
        :param value: The value of that option (if there is a value)
        """
        self.options[option] = value

    def get_option(self, option: str) -> Union[Path, str, int]:
        """
        Get the value of an option associated with the track.
        :param option: The option name (not including the double dashes)
        :return: The value stored in the parameter
        """
        return self.options[option]


class MkvSource:
    """
    A Matroska source object.
    """

    source_file: Path
    __tracks: List[MkvSourceTrack]

    def __init__(self, source_file: Union[str, Path]) -> None:
        """
        Create a Matroska source object.
        :param source_file: The file to use as a source
        """
        self.source_file = Path(source_file)
        self.__tracks = list()

    def add_track(self, track: MkvSourceTrack) -> None:
        """
        Add an MkvSourceTrack to the source
        :param track: The MkvSourceTrack to add
        """
        self.__tracks.append(track)

    def remove_track(self, track: MkvSourceTrack) -> None:
        """
        Delete an MkvSourceTrack from the source
        :param track: The MkvSourceTrack to delete
        """
        try:
            self.__tracks.remove(track)
        except ValueError:
            pass

    @property
    def tracks(self) -> List[MkvSourceTrack]:
        """
        Returns a list of all the associated MkvSourceTracks
        :return: List of all associated MkvSourceTracks
        """
        return self.__tracks

    def generate_options(self) -> list:
        """
        Generate all options associated with this source and tracks
        :return: List of all options for the source/tracks
        """
        command = list()
        for track in self.__tracks:
            for k, v in track.options.items():
                if v is not None:
                    command.extend([f"--{k}", f"{track.track}:{v}"])
                else:
                    command.extend([f"--{k}"])
        command.extend(("(", f"{self.source_file.absolute()}", ")"))
        return command


class MkvAttachment:
    """
    A Matroska attachment object.  Very useful for adding things like fonts for subtitle sources/tracks.
    """

    filename: Path
    mime_type: str
    name: str

    def __init__(self, name: str, mime_type: str, filename: Union[str, Path]) -> None:
        """
        Create a subtitle attachment
        :param name: The filename to attach as
        :param mime_type: The MIME type of the fime
        :param filename: The actual file to attach from the local filesystem
        """
        self.name = name
        self.mime_type = mime_type
        self.filename = Path(filename)

    def generate_options(self) -> list:
        """
        Generate all options associated with the attachment.
        :return: List of attachment options passed to mkvmerge
        """
        return [
            "--attachment-name",
            self.name,
            "--attachment-mime-type",
            self.mime_type,
            "--attach-file",
            str(self.filename.absolute()),
        ]


class Matroska:
    """
    A class that contains all the sources, attachments, and options required to create an
    actual useful set of configuration options.  It will also mux everything together.
    """

    attachments: List[MkvAttachment]
    global_options: dict
    mkvmerge_path: Path
    output: Path
    sources: List[MkvSource]
    track_order_override: list

    def __init__(self, output: Union[str, Path]) -> None:
        """
        Create a Matroska muxing object
        :param output: The output file to mux everything into.
        """
        self.sources = list()
        self.attachments = list()
        self.track_order_override = list()
        self.output = Path(output)
        self.mkvmerge_path = Path(shutil.which("mkvmerge"))

    def add_source(self, source: MkvSource) -> None:
        """
        Add an MkvSource to mux into the Matroska file
        :param source: An MkvSource object
        """
        self.sources.append(source)

    def add_attachment(self, attachment: MkvAttachment) -> None:
        """
        Add an MkvAttachment to mux into the Matroska file
        :param attachment: An MkvAttachment object
        """
        self.attachments.append(attachment)

    @property
    def track_order(self) -> list:
        """
        The track order that will be used when muxing.  Automatically generated unless the
        track_order_override parameter is used
        :return: The track order
        """
        if self.track_order_override:
            return self.track_order_override
        temp = list()
        for i in range(0, len(self.sources)):
            for j in self.sources[i].tracks:
                temp.append(f"{i}:{j.track}")
        return temp

    def generate_options(self) -> list:
        """
        Generate a list of options to feed the 'mkvmerge' binary.
        :return: A list of 'mkvmerge' options
        """
        full_command = ["--output", f"{self.output.absolute()}"]
        for k, v in self.global_options.items():
            if not v:
                full_command.append(f"--{k}")
            else:
                full_command.extend([f"--{k}", f"{v}"])
        for source in self.sources:
            full_command.extend(source.generate_options())
        for attachment in self.attachments:
            full_command.extend(attachment.generate_options())
        full_command.extend(["--track-order", ",".join(self.track_order)])
        return full_command

    def mux(
        self,
        filename: Union[str, Path] = None,
        delete_temp: bool = False,
        verbose: bool = False,
    ) -> int:
        """
        Mux all of the included sources, attachemts, and options.
        :param filename: The filename to store the 'mkvmerge' options as JSON
        :param delete_temp: Delete the JSON file after muxing is finished
        """
        if not filename:
            output_file = NamedTemporaryFile(mode="w", delete=False)
        else:
            output_file = Path("output.json").open("w")
        command = f'"{self.mkvmerge_path}" "@{output_file.name}"'
        if verbose:
            print(command)
            print(f"Creating temp file: {output_file.name}")
        with output_file as f:
            json.dump(self.generate_options(), f)
        if verbose:
            results = subprocess.run(shlex.split(command))
        else:
            results = subprocess.run(
                shlex.split(command),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        if delete_temp:
            Path(output_file.name).unlink()
        return results.returncode
