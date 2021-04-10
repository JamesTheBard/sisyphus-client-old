from typing import Union
from wcmatch.pathlib import Path
from typing import NamedTuple, List
from fontTools import ttLib
import sys

FONT_FAMILY_SPECIFIER = 1
FONT_SUBFAMILY_SPECIFIER = 2
FONT_NAME_SPECIFIER = 4


class Font(NamedTuple):
    name: str
    family: str
    subfamily: list
    file: Path


class Style(NamedTuple):
    style: str
    family: str
    subfamily: list


class SubtitleInfo:
    input_file: Path
    styles: List[Style]

    def __init__(self, input_file: Union[str, List]):
        self.input_file = Path(input_file)
        self.styles = list()
        self.__generate_style_map()

    def __generate_style_map(self) -> None:
        with self.input_file.open('r') as f:
            subtitles = f.readlines()
        subtitles = [i for i in subtitles if i.startswith('Style: ')]
        styles = [i.split(',') for i in subtitles]
        for style in styles:
            subfamily = list()
            s = style[0].split(': ')[1]
            family = style[1]
            if int(style[7]):
                subfamily.append("Bold")
            if int(style[8]):
                subfamily.append("Italic")
            if not subfamily:
                subfamily.append("Regular")
            style_info = Style(
                style=s,
                family=family,
                subfamily=subfamily
            )
            self.styles.append(style_info)


def get_info(font_file: Union[Path]) -> Font:
    font = ttLib.TTFont(str(font_file))
    name = str()
    family = str()
    subfamily = str()
    for record in font['name'].names:
        if record.nameID == FONT_NAME_SPECIFIER and not name:
            if b'\000' in record.string:
                name = str(record.string, 'utf-16-be').encode('utf-8')
            else:
                name = record.string
        elif record.nameID == FONT_FAMILY_SPECIFIER and not family:
            if b'\000' in record.string:
                family = str(record.string, 'utf-16-be').encode('utf-8')
            else:
                family = record.string
        elif record.nameID == FONT_SUBFAMILY_SPECIFIER and not subfamily:
            if b'\000' in record.string:
                subfamily = str(record.string, 'utf-16-be').encode('utf-8')
            else:
                subfamily = record.string
        if name and family and subfamily:
            break
    subfamily = [i if i != "Oblique" else "Italic" for i in subfamily.decode().split(' ')]
    return Font(
        name=name.decode(),
        family=family.decode(),
        subfamily=subfamily,
        file=font_file
    )


def generate_font_map(font_directory: Path) -> List[Font]:
    font_directory = Path(font_directory)
    font_map = list()
    for file in font_directory.iterdir():
        if file.suffix == '.ttf':
            font_map.append(get_info(file))
    return font_map


def generate_style_map(subtitle_file: Path) -> List[Style]:
    with subtitle_file.open('r') as f:
        subtitles = f.readlines()
    subtitles = [i for i in subtitles if i.startswith('Style: ')]
    styles = [i.split(',') for i in subtitles]
    style_map = list()
    for style in styles:
        subfamily = list()
        s = style[0].split(': ')[1]
        family = style[1]
        if int(style[7]):
            subfamily.append("Bold")
        if int(style[8]):
            subfamily.append("Italic")
        if not subfamily:
            subfamily.append("Regular")
        style_info = Style(
            style=s,
            family=family,
            subfamily=subfamily
        )
        style_map.append(style_info)
    return style_map


def generate_font_list(font_map: List[Font], style_map: List[Style]) -> List[Font]:
    fonts = list()
    for s in style_map:
        p = [i for i in font_map if i.family == s.family and not (set(i.subfamily) ^ set(s.subfamily))]
        if len(p) == 1:
            fonts.append(p[0])
        else:
            raise FontNotFoundError(style=s)
    return remove_duplicates(fonts)


def remove_duplicates(font_map: List[Font]) -> List[Font]:
    new_map = list()
    for font in font_map:
        if font.file not in [i.file for i in new_map]:
            new_map.append(font)
    return new_map


class FontError(Exception):
    pass


class FontNotFoundError(FontError):

    def __init__(self, style: Style, message: str = "Font file missing for a Style."):
        self.message = message
        self.style = style
