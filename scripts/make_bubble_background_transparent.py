from __future__ import annotations

import argparse
from collections import deque
from pathlib import Path

from PIL import Image


def is_exterior_white(pixel: tuple[int, int, int, int]) -> bool:
    red, green, blue, alpha = pixel
    return alpha == 0 or (min(red, green, blue) >= 220 and max(red, green, blue) - min(red, green, blue) <= 24)


def remove_edge_connected_white(source: Path, target: Path) -> None:
    with Image.open(source) as opened:
        image = opened.convert("RGBA")
    width, height = image.size
    pixels = image.load()
    visited = bytearray(width * height)
    queue: deque[tuple[int, int]] = deque()

    def enqueue(x: int, y: int) -> None:
        index = y * width + x
        if visited[index] or not is_exterior_white(pixels[x, y]):
            return
        visited[index] = 1
        queue.append((x, y))

    for x in range(width):
        enqueue(x, 0)
        enqueue(x, height - 1)
    for y in range(height):
        enqueue(0, y)
        enqueue(width - 1, y)

    while queue:
        x, y = queue.popleft()
        red, green, blue, _ = pixels[x, y]
        pixels[x, y] = (red, green, blue, 0)
        if x:
            enqueue(x - 1, y)
        if x + 1 < width:
            enqueue(x + 1, y)
        if y:
            enqueue(x, y - 1)
        if y + 1 < height:
            enqueue(x, y + 1)

    alpha = image.getchannel("A")
    if alpha.getextrema() == (0, 0):
        image.close()
        raise ValueError("background removal produced a fully transparent image")
    if any(alpha.getpixel(point) != 0 for point in ((0, 0), (width - 1, 0), (0, height - 1), (width - 1, height - 1))):
        image.close()
        raise ValueError("one or more image corners are not transparent")
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, format="PNG", optimize=True)
    image.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    remove_edge_connected_white(args.input, args.output)


if __name__ == "__main__":
    main()
