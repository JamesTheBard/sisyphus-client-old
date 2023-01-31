import os
import platform
import uuid
from pathlib import Path


class Config:
    VERSION = "1.8.0"
    API_URL = os.environ.get("SISYPHYS_SERVER", "http://127.0.0.1:5000")
    API_FAILURE_DELAY = 10

    HOSTNAME = os.getenv("HOSTNAME_OVERRIDE", platform.node())
    HOST_UUID = str(uuid.uuid4())

    # Ffmpeg Module Options
    # FFMPEG_BIN_PATH = "/usr/bin/ffmpeg"
    # FFMPEG_MONGO_DB = "profiles"
    # FFMPEG_MONGO_COLLECTION = "encoding"
    # FFMPEG_MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:root@localhost:27017/profiles?authSource=admin")

    # Mkvmerge Module Options
    MKVMERGE_ENABLE_FONT_ATTACHMENTS = True
    MKVMERGE_FONT_DIRECTORY = Path(
        os.getenv("FONT_DIRECTORY", "/mnt/phoenix/Server/fonts")
    )
