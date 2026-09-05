from pathlib import Path
import sys

from PIL import Image


def main(source: str, target: str) -> None:
    source_path = Path(source)
    target_path = Path(target)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source_path) as image:
        rgba = image.convert("RGBA")
        rgba.save(
            target_path,
            format="ICO",
            sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
        )


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: prepare_icon.py source.png target.ico")
    main(sys.argv[1], sys.argv[2])
