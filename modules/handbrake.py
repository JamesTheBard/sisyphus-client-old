import os
from pathlib import Path
from modules.base import BaseModule
from modules.exceptions import JobValidationError
from helpers.handbrake import Handbrake as Hb
from helpers.handbrake import HandbrakeTrack


class Handbrake(BaseModule):

    def __init__(self, data: dict, job_title: str):
        super().__init__(data, job_title)
        self.module_name = 'handbrake'
        self.encoder = Hb()
        self.encoder.cli_path = Path(os.getenv('HANDBRAKE_CLI_PATH', self.encoder.cli_path))

    def process_data(self):
        self.encoder.source = self.data.source
        self.encoder.output_file = self.data.output_file

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

        track_sections = [
            "audio",
            "subtitle",
        ]
        for section in track_sections:
            try:
                for track in self.data[f'{section}_tracks']:
                    a = getattr(self.encoder, f'{section}_tracks')
                    a.append(HandbrakeTrack(**track))
            except KeyError:
                pass

    def run(self):
        self.process_data()
        command = self.encoder.generate_cli()

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
