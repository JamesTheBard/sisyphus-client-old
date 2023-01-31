import argparse
import sys
from pathlib import Path

from config import Config
from helpers.font import (
    FontNotFoundError,
    generate_font_list,
    generate_font_map,
    generate_style_map,
)

parser = argparse.ArgumentParser(description="Find missing fonts in ASS/SSA styles")
parser.add_argument("-s", "--subtitle", help="Subtitle file to analyze.", required=True)
args = parser.parse_args()

font_map = generate_font_map(Path(Config.MKVMERGE_FONT_DIRECTORY))
style_map = generate_style_map(Path(args.subtitle))
try:
    font_list = generate_font_list(font_map, style_map)
except FontNotFoundError as e:
    print(
        f"Could not find a font for style '{e.style.style}': font => '{e.style.family}/{'+'.join(e.style.subfamily)}'"
    )
    sys.exit(1)

print("All fonts found, no issues detected.")
