# game-gen-skill

A Codex-native game generation skill for building browser games and game-ready 2D assets without Higgsfield CLI.

The skill keeps the useful parts of the original game-generation workflow — game design, a shared visual style contract, asset manifests, local deterministic texture/spritesheet processing, and browser-game assembly — while replacing cloud image generation with Codex's built-in image generation capability.

## What it supports

### 1. Static sprites, backgrounds, and UI

Uses Codex built-in image generation for:

- player and enemy sprites
- props and pickups
- backgrounds
- UI elements and icons
- reference-driven visual variants

All generated visual assets share a single `STYLE FORMULA` so independently generated assets stay visually coherent.

### 2. Seamless textures and PBR maps

Codex image generation creates or edits the source texture, then the bundled local pipeline performs deterministic post-processing:

```text
source / reference image
        ↓
Codex built-in image generation
        ↓
scripts/pipeline.py
        ↓
seamless texture
basecolor
normal
roughness
height
```

The local texture pipeline uses NumPy and Pillow and performs no network calls.

### 3. AutoSprite / 2D animation sheets

The skill generates a complete transparent fixed-grid spritesheet directly with Codex image generation, then normalizes it locally:

```text
character reference
        ↓
Codex built-in image generation
        ↓
transparent animation grid
        ↓
scripts/spritesheet.py
        ↓
game-ready spritesheet
```

There is no video-generation step and no external background-removal service.

### 4. Browser game generation

For full-game requests, the skill can:

- define the game profile and core loop
- create `design/assets.csv`
- derive one shared `STYLE FORMULA`
- generate required 2D assets
- write the browser game
- support keyboard, touch, and optional gamepad input
- use fixed-timestep simulation where appropriate
- verify the game locally over HTTP

The result is source code and local project files. This skill does not perform hosted deployment.

## What was intentionally removed

This repository does **not** use Higgsfield CLI.

The following original capabilities are intentionally out of scope:

- Higgsfield authentication/account management
- Higgsfield model discovery
- Higgsfield image/video/audio/3D generation
- AI 3D mesh generation, rigging, and animation
- AI music, SFX, or voice generation
- hosted game deployment
- marketplace publishing
- hosted online multiplayer infrastructure
- direct OpenAI API image generation
- external image-generation CLIs or provider SDKs

For image creation and image editing, the skill relies on Codex's built-in image generation capability only.

## Repository structure

```text
game-gen-skill/
├── SKILL.md
├── README.md
├── LICENSE
├── references/
│   ├── game-design-system.md
│   ├── stylization.md
│   ├── 2d-animation.md
│   ├── textures.md
│   └── build-game.md
└── scripts/
    ├── pipeline.py
    └── spritesheet.py
```

## Core workflow

```text
Game brief
    ↓
Game design
    ↓
design/assets.csv
    +
STYLE FORMULA
    ↓
Codex built-in image generation
    ├── static sprites / backgrounds / UI
    ├── source textures / texture edits
    └── animation spritesheets
    ↓
Local deterministic processing
    ├── pipeline.py
    └── spritesheet.py
    ↓
Browser-game assembly
    ↓
Local verification
```

## STYLE FORMULA

Every visual asset is generated using one frozen visual-style description.

The formula defines:

- rendering style
- shape and line language
- palette by gameplay role
- lighting and mood
- readability and perspective

The exact same formula should be reused across every generated asset. This is the main mechanism for preventing a game from ending up with unrelated visual styles across sprites, backgrounds, tiles, and UI.

## Asset manifest

Before generating a full game, the skill creates:

```text
design/assets.csv
```

Example:

```csv
id,role,type,description,size/ratio,style line ref,source
hero,player,sprite,small armored adventurer,1:1,style-1,generate
slime,enemy,sprite,round green slime,1:1,style-1,generate
stone_floor,terrain,texture,old mossy stone floor,1:1,style-1,generate
```

The manifest is the contract between game design, asset generation, and game assembly.

## Local texture pipeline

Requirements:

```bash
pip install numpy pillow
```

Example:

```bash
python3 scripts/pipeline.py source.png \
  -o textures/stone
```

With a palette/reference image:

```bash
python3 scripts/pipeline.py generated.png \
  -o textures/stone \
  --ref textures/stone_ref.png
```

Outputs:

```text
stone_seamless.png
stone_basecolor.png
stone_normal.png
stone_roughness.png
stone_height.png
```

Generate PBR maps from an already-seamless texture without modifying the seam:

```bash
python3 scripts/pipeline.py tile.png \
  -o textures/stone \
  --no-seam
```

## Local spritesheet normalization

The generated source sheet should have a known fixed grid and a true transparent background.

Example for a 4 × 3 sheet containing 12 frames:

```bash
python3 scripts/spritesheet.py hero_walk.png \
  --cols 4 \
  --rows 3 \
  --frames 12 \
  --fps 12 \
  --loop \
  -o assets/hero_walk.png
```

The script:

- validates alpha transparency
- slices the declared grid
- computes one union content box across all frames
- applies the same crop to every frame
- preserves pose alignment
- rebuilds a compact row-major sheet
- outputs animation metadata as JSON to stdout

## Using the skill in Codex

Install or make this repository available as a Codex skill, then ask for tasks such as:

```text
Make a small side-view action game with a consistent hand-painted fantasy style.
```

```text
Create a transparent 4x3 walk-cycle spritesheet for this character.
```

```text
Create a seamless mossy stone-floor texture and generate its normal, roughness, and height maps.
```

```text
Create the player sprite, enemy sprites, UI icons, and background for this browser game using one coherent style.
```

The detailed execution rules live in `SKILL.md` and the files under `references/`.

## Design principles

- plan before generating assets
- one visual system per game
- use AI for generative pixels, deterministic code for processing
- prefer transparent assets directly instead of chroma-key workflows
- keep generated assets project-local before wiring them into code
- do not silently fall back to external image APIs or CLIs
- keep browser-game behavior deterministic where practical
- verify locally before delivery

## License

MIT
