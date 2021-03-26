import os
import uuid
import platform
from pathlib import Path
from version import VERSION as V


class Config:
    VERSION = V
    REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
    REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

    REDIS_QUEUE_NAME = 'queue'
    REDIS_COMPLETED_LIST = 'completed'

    UUID_NAMESPACE = uuid.UUID('0067f190-fa1e-461f-9115-6193c804c883')
    HOSTNAME = os.getenv('HOSTNAME_OVERRIDE', platform.node())
    HOST_UUID = str(uuid.uuid5(UUID_NAMESPACE, HOSTNAME))

    # Ffmpeg Module Options
    # FFMPEG_BIN_PATH = "/usr/bin/ffmpeg"
    FFMPEG_MONGO_DB = "profiles"
    FFMPEG_MONGO_COLLECTION = "encoding"
    FFMPEG_MONGO_URI = os.environ.get("MONGO_URI", "mongodb://root:root@localhost:27017/profiles?authSource=admin")

    # Mkvmerge Module Options
    MKVMERGE_ENABLE_FONT_ATTACHMENTS = True
    MKVMERGE_FONT_DIRECTORY = Path(os.getenv('FONT_DIRECTORY', '/mnt/phoenix/Server/fonts'))
