#!/usr/bin/env python3
"""Deterministic game-texture post-process.

Input image -> optional trim -> optional reference palette match -> seamless repair
-> basecolor/normal/roughness/height maps.

This script performs no network calls and invokes no image-generation provider.
It requires only numpy and Pillow.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image


def trim_border(img: Image.Image, frac: float) -> Image.Image:
    if frac <= 0:
        return img
    w, h = img.size
    k = int(min(w, h) * frac)
    if k <= 0 or w - 2 * k < 8 or h - 2 * k < 8:
        return img
    return img.crop((k, k, w - k, h - k))


def match_colors(img: Image.Image, ref: Image.Image) -> Image.Image:
    """Per-channel histogram matching to preserve a reference palette."""
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    r = np.asarray(ref.convert("RGB"), dtype=np.float64)
    out = np.empty_like(a)
    bins = np.arange(257)

    for c in range(3):
        src_hist, _ = np.histogram(a[..., c], bins=bins)
        ref_hist, _ = np.histogram(r[..., c], bins=bins)
        src_cdf = np.cumsum(src_hist).astype(np.float64)
        ref_cdf = np.cumsum(ref_hist).astype(np.float64)
        src_cdf /= max(src_cdf[-1], 1.0)
        ref_cdf /= max(ref_cdf[-1], 1.0)
        lut = np.interp(src_cdf, ref_cdf, np.arange(256))
        out[..., c] = lut[a[..., c].astype(np.uint8)]

    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def periodic_component(arr: np.ndarray) -> np.ndarray:
    """Moisan-style periodic decomposition to reduce opposite-edge mismatch."""
    arr = arr.astype(np.float64)
    h, w = arr.shape[:2]
    out = np.empty_like(arr)

    fy = np.cos(2 * np.pi * np.arange(h) / h)[:, None]
    fx = np.cos(2 * np.pi * np.arange(w) / w)[None, :]
    denom = 2 * fy + 2 * fx - 4
    denom[0, 0] = 1.0

    for c in range(arr.shape[2]):
        u = arr[..., c]
        v = np.zeros_like(u)
        v[0, :] += u[-1, :] - u[0, :]
        v[-1, :] += u[0, :] - u[-1, :]
        v[:, 0] += u[:, -1] - u[:, 0]
        v[:, -1] += u[:, 0] - u[:, -1]
        smooth = np.fft.fft2(v) / denom
        smooth[0, 0] = 0.0
        out[..., c] = u - np.real(np.fft.ifft2(smooth))

    return np.clip(out, 0, 255)


def _wrap_blur(a: np.ndarray, sigma: float) -> np.ndarray:
    fy = np.fft.fftfreq(a.shape[0])[:, None]
    fx = np.fft.fftfreq(a.shape[1])[None, :]
    kernel = np.exp(-2 * (np.pi * sigma) ** 2 * (fy**2 + fx**2))
    return np.real(np.fft.ifft2(np.fft.fft2(a) * kernel))


def flatten_luminance(arr: np.ndarray, sigma_frac: float = 0.07) -> np.ndarray:
    """Reduce broad lighting drift that becomes visible as a repeated grid."""
    arr = arr.astype(np.float64)
    h, w = arr.shape[:2]
    lum = arr.mean(axis=2)
    sigma = max(1.0, sigma_frac * min(h, w))
    low = _wrap_blur(lum, sigma)
    return np.clip(arr + (low.mean() - low)[..., None], 0, 255)


def _blend_axis(arr: np.ndarray, axis: int, overlap: float) -> np.ndarray:
    """Move the wrap seam to the center and replace it gradually with center texture."""
    n = arr.shape[axis]
    shift = n // 2
    rolled = np.roll(arr, shift, axis=axis)
    k = max(2, int(n * overlap / 2))
    c = n // 2

    start = max(0, c - k)
    stop = min(n, c + k)
    width = stop - start
    if width < 2:
        return arr

    dst_slice = [slice(None)] * 3
    dst_slice[axis] = slice(start, stop)

    donor_idx = np.arange(start, stop)
    donor = np.take(arr, donor_idx, axis=axis)
    band = rolled[tuple(dst_slice)]

    x = np.linspace(-1.0, 1.0, width)
    alpha = 0.5 * (1.0 + np.cos(np.pi * x))
    shape = [1, 1, 1]
    shape[axis] = width
    alpha = alpha.reshape(shape)

    rolled[tuple(dst_slice)] = band * (1.0 - alpha) + donor * alpha
    return np.roll(rolled, -shift, axis=axis)


def make_seamless(img: Image.Image, overlap: float = 0.18) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float64)
    arr = flatten_luminance(arr)
    arr = periodic_component(arr)
    arr = _blend_axis(arr, 1, overlap)
    arr = _blend_axis(arr, 0, overlap)
    arr = periodic_component(arr)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")


def pbr_maps(img: Image.Image, normal_strength: float = 2.0) -> dict[str, Image.Image]:
    rgb = np.asarray(img.convert("RGB"), dtype=np.float64)
    lum = rgb.mean(axis=2) / 255.0

    # Multi-scale luminance gives a useful generic height proxy without baking
    # broad lighting gradients into the height field.
    height = _wrap_blur(lum, 2.0) - _wrap_blur(lum, 36.0)
    lo, hi = np.percentile(height, [1, 99])
    height = np.clip((height - lo) / (hi - lo + 1e-9), 0, 1)

    gx = (np.roll(height, -1, axis=1) - np.roll(height, 1, axis=1)) * normal_strength
    gy = (np.roll(height, -1, axis=0) - np.roll(height, 1, axis=0)) * normal_strength
    nz = np.ones_like(gx)
    norm = np.sqrt(gx * gx + gy * gy + nz * nz)
    normal = np.stack(
        [(-gx / norm + 1.0) * 0.5, (gy / norm + 1.0) * 0.5, (nz / norm + 1.0) * 0.5],
        axis=-1,
    )

    local = lum - _wrap_blur(lum, 6.0)
    roughness = np.clip(0.72 - np.abs(local) * 1.8, 0.18, 0.95)

    def gray(a: np.ndarray) -> Image.Image:
        return Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8), "L")

    return {
        "basecolor": img.convert("RGB"),
        "normal": Image.fromarray((np.clip(normal, 0, 1) * 255).astype(np.uint8), "RGB"),
        "height": gray(height),
        "roughness": gray(roughness),
    }


def seam_ratio(img: Image.Image) -> float:
    a = np.asarray(img.convert("RGB"), dtype=np.float64)
    seam = np.abs(a[0] - a[-1]).mean() + np.abs(a[:, 0] - a[:, -1]).mean()
    base = np.abs(np.diff(a, axis=0)).mean() + np.abs(np.diff(a, axis=1)).mean()
    return float(seam / max(base, 1e-9))


def run(
    input_path: str,
    prefix: str,
    ref_path: str | None = None,
    trim: float = 0.0,
    overlap: float = 0.18,
    do_seam: bool = True,
    normal_strength: float = 2.0,
) -> dict:
    out = Path(prefix)
    out.parent.mkdir(parents=True, exist_ok=True)

    img = Image.open(input_path).convert("RGB")
    img = trim_border(img, trim)

    if ref_path:
        img = match_colors(img, Image.open(ref_path).convert("RGB"))

    if do_seam:
        img = make_seamless(img, overlap=overlap)

    seamless_path = f"{prefix}_seamless.png"
    img.save(seamless_path)

    files = {"seamless": seamless_path}
    for name, mapped in pbr_maps(img, normal_strength=normal_strength).items():
        path = f"{prefix}_{name}.png"
        mapped.save(path)
        files[name] = path

    result = {
        "input": str(input_path),
        "reference": str(ref_path) if ref_path else None,
        "seam_ratio": round(seam_ratio(img), 4),
        "files": files,
    }
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    p = argparse.ArgumentParser(description="Make a texture seamless and derive generic PBR maps.")
    p.add_argument("input", help="source image")
    p.add_argument("-o", "--prefix", required=True, help="output prefix, e.g. textures/stone")
    p.add_argument("--ref", default=None, help="optional reference image for palette matching")
    p.add_argument("--trim", type=float, default=0.0, help="fraction trimmed from every edge")
    p.add_argument("--overlap", type=float, default=0.18, help="center blend corridor fraction")
    p.add_argument("--no-seam", action="store_true", help="skip seam repair and generate maps only")
    p.add_argument("--normal-strength", type=float, default=2.0, help="generic normal-map strength")
    args = p.parse_args()

    run(
        args.input,
        args.prefix,
        ref_path=args.ref,
        trim=args.trim,
        overlap=args.overlap,
        do_seam=not args.no_seam,
        normal_strength=args.normal_strength,
    )


if __name__ == "__main__":
    main()
