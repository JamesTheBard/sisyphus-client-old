FROM ubuntu:rolling

WORKDIR /app

RUN apt-get update && \
    apt-get install -y \
        ffmpeg \
        handbrake-cli \
        mkvtoolnix \
        libmediainfo-dev \
        python3-pip

COPY app /app

RUN pip3 install -r requirements.txt

CMD [ "python3", "sisyphus.py" ]
