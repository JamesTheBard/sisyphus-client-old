FROM ubuntu:rolling

WORKDIR /app

COPY app /app

RUN apt-get update && \
    apt-get install -y \
        ffmpeg \
        handbrake-cli \
        mkvtoolnix \
        libmediainfo-dev \
        python3-pip && \
    pip3 install -r requirements.txt

CMD [ "python3", "sisyphus.py" ]
