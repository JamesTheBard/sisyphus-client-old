from pathlib import Path

from modules import exceptions as ex
from modules.base import BaseModule


class Cleanup(BaseModule):
    def __init__(self, data: dict, job_title: str):
        super().__init__(data, job_title)
        self.module_name = "cleanup"

    def command_parser(self, command: str):
        try:
            func = getattr(self, f"c_{command}")
        except AttributeError:
            raise ex.JobConfigurationError(
                message=f"There is no '{command}' function defined in the module.",
                module=self.module_name,
            )
        return func

    def run(self):
        for k, v in self.data.items():
            self.command_parser(k)(v)

    def c_verify_exists(self, data):
        for f in [Path(i) for i in data]:
            if not f.exists:
                raise ex.JobRunFailureError(
                    message=f"Cannot verify file '{f.absolute()}' exists.",
                    module=self.module_name,
                )

    @staticmethod
    def c_delete_files(data):
        for f in [Path(i) for i in data]:
            f.unlink(missing_ok=True)

    @staticmethod
    def c_copy_files(data):
        pass
