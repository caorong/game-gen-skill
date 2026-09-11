# AutoSprite: Codex-Native 2D Animation Sheets

Use this reference for animated 2D game assets delivered as spritesheets. This version intentionally uses only Codex's built-in `image_gen` capability plus local deterministic post-processing. It does not create animation video, call an external video model, or use a background-removal service.

Read `stylization.md` first. Every generated sheet must include the game's STYLE FORMULA verbatim.

## 1. Strategy

Generate **one complete spritesheet per action and direction** in a single built-in image-generation call, then normalize its cells locally.

The single-sheet approach is preferred over generating frames one by one because independent frame calls drift in face, costume, proportions, palette, and silhouette.

Typical outputs:

```text
hero_idle.png
hero_walk.png
hero_attack.png
slime_idle.png
slime_hit.png
```

After local normalization, use metadata-rich names such as:

```text
hero_idle_f16_192x256_g4x4_fps12_loop.png
hero_attack_f12_192x256_g4x3_fps14_once.png
```

## 2. Source identity

If a canonical base sprite already exists, use it as the identity reference for every animation sheet. Make the local file visible to Codex's image workflow before generation/editing.

If no base sprite exists, first generate one with the static-sprite rules from `stylization.md`:

- full subject visible;
- same perspective intended for animation;
- neutral readable pose;
- true transparent background;
- no text, border, ground, or unrelated props.

Do not redesign the character independently per action.

## 3. One action per sheet

Each sheet contains exactly one action. Good action names include:

- `idle`
- `walk`
- `run`
- `attack`
- `cast`
- `hit`
- `death`
- `jump`
- `pickup`
- `interact`

Do not combine multiple verbs such as `run and shoot and turn around` in one sheet. If direction changes are needed, generate one sheet per direction unless the game intentionally mirrors one side.

## 4. Choose a strict grid

Prefer a small fixed grid that the image model can visually maintain.

Suggested defaults:

| Motion | Frames | Grid |
|---|---:|---:|
| idle / breathing / hover | 8 | 4×2 |
| walk / run, pixel-art | 8 | 4×2 |
| walk / run, HD | 12 | 4×3 |
| attack / hit / jump | 12 | 4×3 |
| detailed loop | 16 | 4×4 |
| fluid FX | 16 | 4×4 |

Prefer 8, 12, or 16 frames. Larger sheets are harder for an image model to keep structurally exact and usually add little gameplay value.

If the user explicitly needs a different count, choose a compact grid and state it before generation.

## 5. Sheet prompt contract

The image-generation prompt must specify all of these:

- use case: game animation spritesheet;
- exact action;
- exact grid dimensions and exact frame count;
- frame order: left-to-right, then top-to-bottom;
- same character identity in every cell;
- same costume, proportions, palette, view, camera, scale, and lighting in every cell;
- subject fully inside every cell with consistent margin;
- same facing direction in every frame unless the action itself is a turn;
- transparent background;
- no grid lines, cell labels, numbers, text, captions, border, shadow plane, or decorative background;
- motion should progress smoothly across cells.

For loops, explicitly request a seamless cyclic progression where the last pose flows naturally back into the first. Do **not** request a duplicated final frame identical to frame 1; duplicate timing can be handled in game code if ever needed.

Prompt shape:

```text
Use case: game animation spritesheet.
Create exactly <N> frames of <ACTION> for the same <CHARACTER DESCRIPTION>, arranged as an invisible <COLS>x<ROWS> uniform grid, ordered left-to-right then top-to-bottom.
Every cell must show the exact same character identity, costume, body proportions, palette, camera angle, scale, lighting, and facing direction. Keep the full body inside every cell with equal transparent margin. Motion progresses smoothly frame to frame.
<STYLE FORMULA>
True transparent background. No grid lines, no labels, no numbers, no text, no border, no scenery, no ground plane, no cast shadow outside the character.
```

For a loop append:

```text
The sequence is cyclic: the final pose must flow naturally back into the first pose without duplicating the first frame.
```

For a one-shot append the intended anticipation → action → follow-through structure.

## 6. Direction rules

For side-view games, prefer one canonical facing direction and mirror in engine only when asymmetry does not matter. Do not mirror characters with direction-sensitive text, shield/weapon placement, scars, or asymmetric equipment unless the design accepts that change.

For top-down/isometric games, generate separate directional sheets when the silhouette materially changes. Keep the same action timing and grid across directions.

## 7. Built-in image generation only

Use Codex's built-in `image_gen`. Do not call an image CLI, API, video generator, or provider SDK.

For a local base sprite, first load/view it so the built-in image workflow can use it as a reference. Preserve it aggressively; the animation request should change pose over time, not redesign the subject.

Copy the selected generated sheet into the project, for example:

```text
assets/generated/hero_idle_source.png
```

Do not leave the game referencing an image only under Codex's generated-image cache.

## 8. Local normalization

Run the bundled script after each accepted source sheet:

```bash
python3 "$GAME_SKILL/scripts/spritesheet.py" \
  assets/generated/hero_idle_source.png \
  --cols 4 --rows 4 --frames 16 \
  --fps 12 --loop \
  -o assets/hero_idle.png
```

The script:

1. slices the source into the declared equal grid;
2. verifies useful alpha exists;
3. finds the union alpha bounding box across frames;
4. crops every frame to the same union box so local post-processing does not introduce jitter;
5. adds optional padding;
6. writes a compact normalized sheet preserving frame order;
7. prints machine-readable metadata including frame count, grid, cell size, FPS, and loop mode.

This script can normalize layout; it cannot fix semantic generation errors such as a changing face, wrong weapon, duplicated limbs, incorrect action order, or inconsistent perspective.

## 9. Acceptance gate

Inspect the sheet before wiring it into the game. Reject/regenerate when any of these are materially wrong:

- character identity changes between cells;
- equipment appears/disappears unexpectedly;
- facing direction flips;
- camera angle or scale drifts;
- subject is cropped;
- background is not truly transparent;
- the declared number of cells is not present;
- cell order is ambiguous;
- action contains an unrelated motion;
- loop has an obvious discontinuity that cannot be hidden by timing.

A generation failure gets at most two retries. Retry the same core prompt first; sampling variance often causes a one-off bad sheet. Change prompt structure only when the failure repeats systematically.

## 10. Engine playback

Frame order is row-major: left-to-right, top-to-bottom. Use the normalized output's reported cell width/height.

For loops, wrap from `frame_count - 1` to `0`. For one-shots, stop or transition after the final frame.

Keep animation FPS in data/config rather than hard-coding it into rendering logic. Attack gameplay timing may use explicit hit windows rather than assuming the visual midpoint is always the damage frame.

## 11. Pixel art

For pixel-art sheets:

- use the same pixel-art STYLE FORMULA as the static character;
- keep all cells on the same apparent pixel grid;
- prefer 8 or 12 frames rather than excessive interpolation;
- use nearest-neighbor resizing only;
- inspect at 100% and an integer zoom.

## 12. Limits

Direct image-generated spritesheets trade motion precision for character consistency and simplicity. They work best for compact stylized animation sets. If the requested motion requires highly accurate choreography, physically exact transitions, or long cinematic movement, this route may not be sufficient; do not silently introduce a video/3D provider because this skill explicitly excludes those dependencies.
