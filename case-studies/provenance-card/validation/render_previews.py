#!/usr/bin/env python3
"""Render the checked SVGs as convenience PNG previews with local Firefox."""

from pathlib import Path
import struct
import subprocess
import tempfile


CARD = Path(__file__).resolve().parents[1]
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def render(svg_name: str, png_name: str, width: int, height: int) -> None:
    svg = CARD / svg_name
    png = CARD / png_name
    if not svg.is_file() or png.exists():
        raise RuntimeError(f"expected an existing {svg_name} and absent {png_name}")
    with tempfile.TemporaryDirectory(prefix="provenance-firefox-") as profile:
        completed = subprocess.run(
            ["firefox", "--headless", "--no-remote", "--profile", profile,
             "--screenshot", str(png), "--window-size", f"{width},{height}",
             svg.as_uri()],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    if completed.returncode:
        raise RuntimeError(f"Firefox failed to render {svg_name}: exit {completed.returncode}")
    header = png.read_bytes()[:24]
    if len(header) != 24 or header[:8] != PNG_SIGNATURE:
        raise RuntimeError(f"Firefox did not write a PNG for {svg_name}")
    dimensions = struct.unpack(">II", header[16:24])
    if dimensions != (width, height):
        raise RuntimeError(f"unexpected dimensions for {png_name}: {dimensions}")


if __name__ == "__main__":
    render("card.svg", "card-1280.png", 1280, 920)
    render("card-mobile.svg", "card-360.png", 360, 1630)
