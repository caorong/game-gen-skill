#!/usr/bin/env python3
"""Normalize a fixed-grid transparent spritesheet.

The script does not generate images. It slices a declared grid, validates alpha,
finds one union content box across all used frames, crops every frame with that
same box, optionally pads it, and writes a compact row-major output sheet.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from PIL import Image


def cell_bounds(size: int, count: int) -> list[int]:
    # Rounded boundaries tolerate source dimensions that are not exactly divisible.
    return [round(i * size / count) for i in range(count + 1)]


def alpha_bbox(frame: Image.Image, threshold: int) -> tuple[int, int, int, int] | None:
    alpha = frame.getchannel("A")
    if threshold > 0:
        alpha = alpha.point(lambda v: 255 if v > threshold else 0)
    return alpha.getbbox()


def normalize(
    input_path: str,
    output_path: str,
    cols: int,
    rows: int,
    frames: int,
    fps: float,
    loop: bool,
    padding: int,
    alpha_threshold: int,
) -> dict:
    if cols < 1 or rows < 1:
        raise ValueError("cols and rows must be >= 1")
    if frames < 1 or frames > cols * rows:
        raise ValueError("frames must be between 1 and cols*rows")
    if padding < 0:
        raise ValueError("padding must be >= 0")

    src = Image.open(input_path).convert("RGBA")
    if src.getchannel("A").getextrema() == (255, 255):
        raise ValueError(
            "input has no transparent pixels; regenerate with true transparent background"
        )

    xs = cell_bounds(src.width, cols)
    ys = cell_bounds(src.height, rows)

    raw_frames: list[Image.Image] = []
    boxes: list[tuple[int, int, int, int]] = []
    warnings: list[str] = []

    for index in range(frames):
        r, c = divmod(index, cols)
        cell = src.crop((xs[c], ys[r], xs[c + 1], ys[r + 1]))
        box = alpha_bbox(cell, alpha_threshold)
        if box is None:
            raise ValueError(f"frame {index} is fully transparent")

        if box[0] <= 1 or box[1] <= 1 or box[2] >= cell.width - 1 or box[3] >= cell.height - 1:
            warnings.append(f"frame {index} content touches or nearly touches a cell edge")

        raw_frames.append(cell)
        boxes.append(box)

    # Use one shared box in cell coordinates. This preserves pose position inside
    # each source cell and avoids post-processing-induced jitter.
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[2] for b in boxes)
    bottom = max(b[3] for b in boxes)

    min_w = min(f.width for f in raw_frames)
    min_h = min(f.height for f in raw_frames)
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(min_w, right + padding)
    bottom = min(min_h, bottom + padding)

    if right <= left or bottom <= top:
        raise ValueError("computed union crop is empty")

    normalized = [f.crop((left, top, right, bottom)) for f in raw_frames]
    cell_w, cell_h = normalized[0].size

    out_cols = min(cols, frames)
    out_rows = math.ceil(frames / out_cols)
    sheet = Image.new("RGBA", (out_cols * cell_w, out_rows * cell_h), (0, 0, 0, 0))

    for index, frame in enumerate(normalized):
        r, c = divmod(index, out_cols)
        sheet.alpha_composite(frame, (c * cell_w, r * cell_h))

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)

    metadata = {
        "source": str(input_path),
        "output": str(output_path),
        "frames": frames,
        "cols": out_cols,
        "rows": out_rows,
        "cell_width": cell_w,
        "cell_height": cell_h,
        "fps": fps,
        "loop": loop,
        "source_grid": {"cols": cols, "rows": rows},
        "union_crop": {"left": left, "top": top, "right": right, "bottom": bottom},
        "warnings": sorted(set(warnings)),
    }
    print(json.dumps(metadata, indent=2))
    return metadata


def default_output(input_path: str, frames: int, cols: int, rows: int, fps: float, loop: bool) -> str:
    p = Path(input_path)
    fps_label = str(int(fps)) if float(fps).is_integer() else str(fps).replace(".", "p")
    mode = "loop" if loop else "once"
    return str(
        p.with_name(
            f"{p.stem}_f{frames}_g{cols}x{rows}_fps{fps_label}_{mode}.png"
        )
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Normalize a transparent fixed-grid spritesheet.")
    p.add_argument("input", help="generated spritesheet PNG")
    p.add_argument("--cols", type=int, required=True, help="source grid columns")
    p.add_argument("--rows", type=int, required=True, help="source grid rows")
    p.add_argument("--frames", type=int, default=None, help="used frames; defaults to cols*rows")
    p.add_argument("--fps", type=float, default=12.0, help="playback metadata")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--loop", action="store_true", help="mark animation as looping")
    mode.add_argument("--once", action="store_true", help="mark animation as one-shot")
    p.add_argument("--padding", type=int, default=2, help="transparent pixels around union crop")
    p.add_argument("--alpha-threshold", type=int, default=4, help="alpha > threshold counts as content")
    p.add_argument("-o", "--output", default=None, help="output PNG path")
    args = p.parse_args()

    frames = args.frames if args.frames is not None else args.cols * args.rows
    loop = bool(args.loop)
    output = args.output or default_output(args.input, frames, args.cols, args.rows, args.fps, loop)

    normalize(
        args.input,
        output,
        cols=args.cols,
        rows=args.rows,
        frames=frames,
        fps=args.fps,
        loop=loop,
        padding=args.padding,
        alpha_threshold=args.alpha_threshold,
    )


if __name__ == "__main__":
    main()
