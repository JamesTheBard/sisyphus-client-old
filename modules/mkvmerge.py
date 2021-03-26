from pathlib import Path

from config import Config
from helpers.mkvmerge import Matroska, MkvSource, MkvSourceTrack, MkvAttachment
from helpers.font import generate_font_map, generate_style_map, generate_font_list, remove_duplicates
from modules import exceptions as ex
from modules.base import BaseModule


class Mkvmerge(BaseModule):

    def __init__(self, data: dict, job_title: str):
        super().__init__(data, job_title)
        self.module_name = 'mkvmerge'
        try:
            self.font_directory = Path(Config.MKVMERGE_FONT_DIRECTORY)
        except AttributeError:
            try:
                if not Config.MKVMERGE_ENABLE_FONT_ATTACHMENTS:
                    raise ex.JobConfigurationError(
                        message=f"The configuration file does not have the font directory defined.",
                        module=self.module_name
                    )
                else:
                    self.font_directory = Path()
            except AttributeError:
                raise ex.JobConfigurationError(
                    message=f"The configuration file does not have the MKVMERGE_ENABLE_FONT_ATTACHMENTS set.",
                    module=self.module_name
                )
        if not self.font_directory.exists or not self.font_directory.is_dir():
            raise ex.JobConfigurationError(
                message=f"The font directory '{self.font_directory}' doesn't exist.",
                module=self.module_name
            )
        self.font_map = generate_font_map(font_directory=self.font_directory)
        self.matroska = Matroska(output=self.data.output_file)

    def run(self):
        self.process_data()
        return_code = self.matroska.mux(delete_temp=True)
        if return_code > 0:
            raise ex.JobRunFailureError(
                message=f"`mkvmerge` command returned exit code {return_code}",
                module=self.module_name
            )

    def process_data(self):
        self.matroska.global_options = self.data.options
        sources = [MkvSource(i) for i in self.data.sources]
        for track in self.data.tracks:
            t = MkvSourceTrack(track=track.track)
            t.options = track.options
            sources[track.source].add_track(t)
        [self.matroska.add_source(i) for i in sources]

        if Config.MKVMERGE_ENABLE_FONT_ATTACHMENTS:
            font_list = list()
            for s in sources:
                if s.source_file.suffix in ['.ssa', '.ass']:
                    style_map = generate_style_map(s.source_file)
                    temp_font_list = generate_font_list(self.font_map, style_map)
                    font_list.extend(temp_font_list)
            font_list = remove_duplicates(font_list)
            for font in font_list:
                a = MkvAttachment(
                    name=str(font.file.name),
                    mime_type='font/sfnt',
                    filename=str(font.file.resolve())
                )
                self.matroska.add_attachment(a)

    def validate(self):
        if len(self.font_map) == 0 and Config.MKVMERGE_ENABLE_FONT_ATTACHMENTS:
            raise ex.JobValidationError(
                message=f"There are no fonts in the font directory '{self.font_directory}'.",
                module=self.module_name
            )
        if len(self.data.sources) == 0:
            raise ex.JobValidationError(
                message=f"There are no source files specified.",
                module=self.module_name
            )
        if len(self.data.tracks) == 0:
            raise ex.JobValidationError(
                message=f"There are no tracks specified.",
                module=self.module_name
            )
        for file in [Path(i) for i in self.data.sources]:
            if not file.exists or not file.is_file():
                raise ex.JobValidationError(
                    message=f"The source file '{file.absolute()}' does not exist.",
                    module=self.module_name
                )
        if "output_file" not in self.data.keys():
            raise ex.JobValidationError(
                message=f"No output file specified.",
                module=self.module_name
            )
