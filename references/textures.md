# Texture Tile Factory with Codex Native Images

Use this reference for seamless/tileable 2D textures and derived PBR maps: ground, walls, floors, roofs, terrain, stone, wood, fabric, and similar repeating surfaces.

The pipeline has two layers:

1. **AI source generation/edit** — Codex built-in `image_gen` only.
2. **Deterministic local finish** — `$GAME_SKILL/scripts/pipeline.py` for seam repair, palette restoration against a reference, and PBR-map generation.

Read `stylization.md` first and include the STYLE FORMULA verbatim in every texture generation/edit request.

## 1. Inputs

The route accepts either:

- a user/reference material image; or
- a material description with no reference.

When a reference exists, crop or select a clean square region without strong perspective, depth-of-field blur, large shadows, text, or a single dominant object. Save it under a stable project path such as:

```text
textures/stone_ref.png
```

## 2. Generate a new texture source

Use Codex built-in `image_gen` to create a square texture source.

Prompt contract:

```text
Use case: game tileable texture source.
Create a square, evenly lit surface texture of <MATERIAL DESCRIPTION>.
<STYLE FORMULA>
Uniform pattern density, orthographic/flat surface view, no perspective, no horizon, no border, no vignette, no text, no watermark, no single focal object, no directional cast shadows. Make the left/right and top/bottom edges visually compatible for repeating tile use.
```

The model is asked for tileability, but local post-processing remains the final authority.

Copy the selected image into the project before running the local script.

## 3. Reference-preserving seamless AI edit

When the user supplied a material reference, prefer an image edit rather than regenerating a different material.

Make the reference visible to the built-in image workflow, then request:

```text
Use case: reference-preserving seamless game texture edit.
Change only what is necessary to make this exact material repeat cleanly across the left/right and top/bottom boundaries.
Preserve the material identity, palette, lighting, scale, pattern density, brush/texture style, and all undamaged interior details.
<STYLE FORMULA>
Do not add or remove semantic objects. No text, border, vignette, perspective, directional shadow, or focal element. Keep the result square and evenly lit.
```

For structured materials such as bricks, planks, roof tiles, or floor tiles, add:

```text
Continue structural rows and unit boundaries coherently across opposite edges; do not smear or dissolve the pattern at the seam.
```

If the edit noticeably restyles the material, retry once with stronger preservation language. Do not keep burning retries on the same strategy; the deterministic local seam repair exists to finish the job.

## 4. Deterministic seam + PBR processing

For a generated source with no material reference:

```bash
python3 "$GAME_SKILL/scripts/pipeline.py" source.png \
  -o textures/stone --trim 0
```

For a reference-preserving edit where exact palette identity matters:

```bash
python3 "$GAME_SKILL/scripts/pipeline.py" edited.png \
  -o textures/stone \
  --ref textures/stone_ref.png \
  --trim 0
```

The script writes:

```text
textures/stone_seamless.png
textures/stone_basecolor.png
textures/stone_normal.png
textures/stone_roughness.png
textures/stone_height.png
```

The local pipeline:

1. optionally trims a border;
2. optionally histogram-matches the image to the reference palette;
3. flattens broad luminance drift;
4. performs periodic seam correction and offset-domain blending;
5. derives height from multi-scale luminance;
6. derives a wrap-safe normal map from the height field;
7. derives a roughness map from local luminance variation.

All filters wrap at image edges so derived maps preserve repeatability.

## 5. Partial routes

### Seam-fix an existing texture

```bash
python3 "$GAME_SKILL/scripts/pipeline.py" tile.png \
  -o textures/tile --trim 0
```

### PBR maps from an already verified seamless texture

```bash
python3 "$GAME_SKILL/scripts/pipeline.py" seamless.png \
  -o textures/tile --trim 0 --no-seam
```

### Trim a known bad border first

```bash
python3 "$GAME_SKILL/scripts/pipeline.py" source.png \
  -o textures/tile --trim 0.04
```

Do not invent a trim percentage to hide semantic defects; trim only when the source actually contains edge contamination.

## 6. Verification

The script prints a seam ratio. Treat it as a diagnostic, not the sole acceptance test.

Also inspect:

1. the basecolor tiled 2×2;
2. a 100% crop across the horizontal wrap;
3. a 100% crop across the vertical wrap;
4. the tile center for accidental blur or repeated ghost elements;
5. normal/height/roughness for unexpected edge lines.

A mathematically small edge difference can still look bad when a recognizable brick, crack, plank, or symbol is cut incorrectly. Human/visual inspection remains required for structured materials.

## 7. Prompt and retry discipline

Retry the AI source/edit only when the **semantic image** is wrong: wrong material, wrong scale, perspective, severe restyling, text, a focal object, or obviously unusable structure.

Do not retry AI merely because the first-pass edges are imperfect. Seam correction is the local script's job.

Use at most two AI retries per material.

## 8. Style consistency

The texture source consumes the exact same STYLE FORMULA as sprites and backgrounds, but readability still matters. Environment texture contrast should not erase foreground silhouettes. A game with stylized characters and photoreal material scans is inconsistent even if each asset looks good alone.

## 9. Output manifest

For projects with multiple materials, keep a simple manifest such as:

```json
{
  "stone": {
    "seamless": "textures/stone_seamless.png",
    "basecolor": "textures/stone_basecolor.png",
    "normal": "textures/stone_normal.png",
    "roughness": "textures/stone_roughness.png",
    "height": "textures/stone_height.png"
  }
}
```

Only list files that actually exist. If a generated material failed visual review, do not silently wire it into the game.
