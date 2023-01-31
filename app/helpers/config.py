import re
from typing import List, NamedTuple, Union

import yaml
from wcmatch.pathlib import Path


class EncoderPreset(NamedTuple):
    name: str
    options: dict


class AutoMatch(NamedTuple):
    regex: str
    title: str
    short_title: str
    season: int

    def generate_title(
        self,
        episode: int,
        release_group: str,
        tail: list = None,
        file_extension: str = ".mkv",
    ) -> Path:
        if not tail:
            tail = ["1080p", "x265-10bit"]
        tail = f"[{']['.join(tail)}]"
        template = f"[{release_group}] {self.title} - {self.season}x{episode:02} {tail}{file_extension}"
        return Path(template)

    def get_episode_number(self, filename: str) -> int:
        if m := re.search(self.regex, filename):
            return int(m.group(1))

    def is_match(self, filename: str) -> bool:
        if re.search(self.regex, filename):
            return True
        return False


class CleanupSetting(NamedTuple):
    name: str
    path: Path
    filters: list

    def clean(self):
        for f in self.files:
            f.unlink()

    @property
    def files(self):
        return [f for f in self.path.glob(self.filters)]


class EncoderConfig:
    audio_presets: List[EncoderPreset]
    automatch_paths: List[Path]
    automatch_settings: List[AutoMatch]
    video_presets: List[EncoderPreset]
    cleanup_settings: List[CleanupSetting]
    config_file: Path
    __config: dict

    def __init__(self, config_file: Union[str, Path] = None):
        if not config_file:
            self.config_file = self.__find_config_file("settings.yaml")
        else:
            self.config_file = Path(config_file)
        self.__config = self.__parse_config_file()
        self.video_presets = self.process_presets(self.video_settings, "video")
        self.audio_presets = self.process_presets(self.audio_settings, "audio")
        self.cleanup_settings = self.process_cleanup()
        self.automatch_settings = self.process_automatch()
        self.automatch_paths = self.config["automatch"]["paths"]
        self.automatch_save_dir = Path(self.config["automatch"]["save_dir"])

    @staticmethod
    def __find_config_file(file_name: str):
        directories = [
            Path.home(),
            Path("/etc/encode-tools"),
            Path("/etc/encode_tools"),
            Path.home().joinpath(".config/encode-tools"),
            Path.home().joinpath(".config/encode_tools"),
            Path(),
        ]
        for d in directories:
            path = d.joinpath(file_name)
            if path.exists():
                return path

    def __parse_config_file(self):
        with self.config_file.open("r") as f:
            config = yaml.safe_load(f)
        return config

    def get_audio_preset(self, name):
        return [i for i in self.audio_presets if i.name == name][0]

    def get_video_preset(self, name):
        return [i for i in self.video_presets if i.name == name][0]

    def process_automatch(self) -> List[AutoMatch]:
        automatch_file = Path(self.config["automatch"]["config"])
        with automatch_file.open("r") as f:
            entries = f.readlines()
        entries = [i.strip() for i in entries if not i.startswith("#")]
        temp = list()
        for entry in entries:
            entry = entry.split("|")
            if len(entry) != 4:
                continue
            e = AutoMatch(
                regex=entry[1],
                title=entry[0],
                short_title=entry[2],
                season=int(entry[3]),
            )
            temp.append(e)
        return temp

    def process_cleanup(self):
        cleanup = list()
        for k, v in self.config["cleanup"].items():
            filters = list()
            if type(v["pattern"]) is str:
                filters = v["pattern"].split("|")
            elif type(v["pattern"]) is list:
                filters = v["pattern"]
            temp = CleanupSetting(
                name=k,
                path=Path(v["path"]),
                filters=filters,
            )
            cleanup.append(temp)
        return cleanup

    def clean_all(self):
        for c in self.cleanup_settings:
            c.clean()

    @staticmethod
    def process_presets(settings, preset_type):
        presets = list()
        for preset_name in settings.keys():
            preset = settings[preset_name]
            temp = {"name": preset_name, "options": dict()}
            try:
                temp["options"]["c"] = preset["codec"]
            except KeyError:
                pass
            try:
                temp["options"]["b"] = preset["bitrate"]
            except KeyError:
                pass
            for k, v in preset.items():
                if k in ["name", "codec", "bitrate"]:
                    continue
                temp["options"][k] = v
            presets.append(EncoderPreset(**temp))
        return presets

    @property
    def config(self):
        return self.__config

    @property
    def video_settings(self):
        return self.__config["encoder"]["video"]["presets"]

    @property
    def audio_settings(self):
        return self.__config["encoder"]["audio"]["presets"]

    @property
    def default_video_preset(self):
        default = self.__config["encoder"]["video"]["default"]
        return [i for i in self.video_presets if i.name == default][0]

    @property
    def default_audio_preset(self):
        default = self.__config["encoder"]["audio"]["default"]
        return [i for i in self.audio_presets if i.name == default][0]
