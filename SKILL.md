---
name: game-gen-skill
description: |
  Build and iterate playable browser games, or create game-specific static sprites,
  backgrounds, UI, seamless textures/PBR maps, and 2D animation spritesheets using
  Codex built-in image generation plus local deterministic processing. Use when the
  user asks to make a browser game, create game art, make a spritesheet/AutoSprite,
  generate or edit a tileable texture, or iterate an existing game with source files.
  This skill intentionally does not use Higgsfield CLI, external image-generation
  CLIs/APIs, 3D generation, audio generation, hosted game deployment, or platform
  multiplayer services.
---

# Game Generation with Codex Native Images

Create coherent game assets and playable browser-game source using Codex's built-in
image generation. Keep AI generation focused on pixels; keep deterministic processing,
assembly, verification, and game logic local.

## Hard provider rule

For every raster generation or raster edit in this skill:

- Use Codex's built-in `image_gen` capability (the installed system image-generation
  workflow), not a shell CLI or direct API.
- Do not request or use `OPENAI_API_KEY`.
- Do not invoke `scripts/image_gen.py`, provider SDKs, Higgsfield CLI, or any external
  image-generation command.
- For a local image that must be edited, first make it visible to the built-in image
  workflow (for example with Codex image viewing), then use the built-in edit flow.
- Built-in generated images normally land under `$CODEX_HOME/generated_images/...`.
  Copy or move the selected result into the project before referencing it from game code.
- Do not overwrite an existing project asset unless the user explicitly asked to replace
  it; otherwise use a versioned sibling filename.
- If built-in image generation is unavailable, do not silently fall back to any API/CLI.
  Continue only with work that does not require new pixels and state the limitation.

## Supported routes

- **Full playable browser game** — plan, generate required 2D assets, build, verify,
  and return the source/project files. No hosted deployment is performed.
- **Static assets only** — sprites, backgrounds, and UI via built-in `image_gen`.
- **Texture only** — generate/edit the texture with built-in `image_gen`, then run the
  local seamless/PBR pipeline.
- **AutoSprite / 2D animation only** — generate a complete animation spritesheet with
  built-in `image_gen`, then normalize and validate it locally.
- **Design only** — produce the requested design artifact and `design/assets.csv`.
- **Existing game iteration** — inspect the supplied source, preserve its architecture
  and unchanged assets, amend the manifest, rebuild, and verify locally.

Out of scope unless the user supplies a separate toolchain: AI 3D generation/rigging,
AI music/SFX/voice, game trailers, online multiplayer backend/platform services,
hosted deployment/marketplace publishing, and native mobile/desktop packaging.
Local same-screen multiplayer is fine because it stays client-side.

## Bootstrap

Locate this installed skill directory and set it explicitly:

```bash
export GAME_SKILL="/absolute/path/to/game-gen-skill"
test -f "$GAME_SKILL/scripts/pipeline.py"
test -f "$GAME_SKILL/scripts/spritesheet.py"
python3 "$GAME_SKILL/scripts/pipeline.py" --help
python3 "$GAME_SKILL/scripts/spritesheet.py" --help
```

Never recreate bundled scripts from memory. If a required bundled script is missing,
stop that route and report the missing path rather than improvising a replacement.

## Full-game workflow

### 1. Plan before generating or coding

Read `references/game-design-system.md` first and in full. Resolve the game profile,
core loop, win/lose/restart behavior, input methods, language handling, and performance
budget.

Create `design/assets.csv` with one row per visual asset:

```csv
id,role,type,description,size/ratio,style line ref,source
```

`source` is `generate` or `reference_media[i]`.

Read `references/stylization.md` before producing any visual. Derive exactly one
STYLE FORMULA for the game and insert it byte-for-byte into every visual-generation
prompt. If the user's brief already fixes the style, state the formula and proceed.
If several materially different styles would change the result, show concise options
and wait for the user's choice.

No generated visual and no game code should exist before `design/assets.csv` and the
STYLE FORMULA are settled.

### 2. Generate assets

Use the reference matching each manifest row:

| Asset | Required reference |
|---|---|
| Static sprites, backgrounds, UI | `references/stylization.md` |
| AutoSprite / 2D animation sheets | `references/2d-animation.md` |
| Repeating ground, walls, tiles, PBR maps | `references/textures.md` |

Independent image generations may run independently. Keep the STYLE FORMULA identical
across every call. Save only selected/final outputs into the project's `assets/`
directory.

Generation failures or obvious style/content failures get at most two retries per asset.
After that, use the best valid result and compensate locally where reasonable, or amend
the manifest honestly.

### 3. Build

Read `references/build-game.md` last, but before writing game code. Build the browser
game with relative asset paths, externalized player-visible strings, deterministic
simulation where applicable, and input support matching the delivery context.

Keep `design/assets.csv` with the project. Missing required assets are a generation-stage
failure; do not silently replace them with unrelated placeholders.

### 4. Verify and deliver

Run locally over HTTP, not `file://`:

```bash
python3 -m http.server 8000
```

Verify the complete game loop, restart, missing assets/404s, console errors, responsive
canvas/layout, physical keyboard codes on non-Latin layouts, touch-only play when mobile
is in scope, declared gamepad controls, fixed-timestep behavior for real-time games, and
local multiplayer with the declared number of players when applicable.

Deliver the project/source path (and ZIP if the user requested one), a one-line gameplay
summary, and any generated asset paths. Do not claim hosted deployment.

## Static image route

Read `references/stylization.md`. Use built-in `image_gen` for sprites, backgrounds, and
UI. Prefer true transparent output for sprites/UI rather than chroma-key backgrounds.
Preserve the approved STYLE FORMULA verbatim.

## Texture route

Read `references/stylization.md` and `references/textures.md`. Use built-in `image_gen`
for the source tile or reference-preserving edit, then use
`$GAME_SKILL/scripts/pipeline.py` for deterministic seam repair and PBR-map generation.
The local post-process, not the image model, is the final authority on tileability.

## AutoSprite route

Read `references/stylization.md` and `references/2d-animation.md`. Use built-in
`image_gen` to create one complete spritesheet per action on a transparent background,
with a strict fixed grid and locked character/view/style. Then run
`$GAME_SKILL/scripts/spritesheet.py` to normalize cell alignment, trim using a union
alpha bound, and write a predictable game-ready sheet.

This route intentionally does not create a video, call a video model, or use a separate
background-removal service.

## Reference order

For full games:

1. `references/game-design-system.md`
2. `references/stylization.md`
3. `references/2d-animation.md` and/or `references/textures.md` only when required
4. `references/build-game.md`

Read selected references completely. Do not load unrelated references.

## UX rules

- Mirror the user's language; keep image-generation prompts in English unless textual
  content inside the asset requires another language.
- Ask only when the answer materially changes the game or art direction.
- Preserve one visual system across generated and procedural assets.
- Never request secrets for this skill.
- Do not describe provider job IDs or internal image-generation mechanics in user-facing
  updates.

## Output by route

- **Design only:** requested design artifact + `design/assets.csv`.
- **Assets only:** usable project-local files and their manifest roles.
- **Texture only:** seamless/basecolor/normal/roughness/height files plus seam check.
- **AutoSprite only:** normalized spritesheet(s), action metadata, and manifest roles.
- **Full game:** locally verified source/project (and ZIP only when requested).
