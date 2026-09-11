# Stylization Contract for Codex-Native Game Art

This reference owns visual consistency across independently generated game assets.
Use it for every sprite, background, UI element, texture source, and AutoSprite sheet.

## 1. One STYLE FORMULA per game

Independent image-generation calls do not remember previous calls. The STYLE FORMULA is the shared visual contract that keeps outputs looking like one game.

Create one English paragraph, roughly 60–90 words, from these blocks in order:

1. **Rendering style** — e.g. chunky pixel art, flat vector cartoon, soft hand-painted gouache.
2. **Shape and line language** — silhouette geometry, outline weight, edge treatment.
3. **Palette by role** — environment base colors, hero contrast colors, signal colors for hazards/pickups.
4. **Light and mood** — one concise clause.
5. **Game readability + perspective** — contrast/readability plus `side-view`, `top-down`, `isometric`, or `flat frontal` as appropriate.

The formula must describe roles, not paint every asset with the same global color cast. The hero should remain readable against the environment; hazards and pickups need a distinct signal treatment.

Do not put asset-specific content, dimensions, file paths, or background-removal instructions into the STYLE FORMULA.

## 2. Byte-identical rule

Insert the approved STYLE FORMULA byte-for-byte into every visual-generation prompt, including retries and later asset additions.

Do not paraphrase it per asset. A style change requested by the user creates a new STYLE FORMULA and may invalidate earlier generated assets.

## 3. Image provider rule

All raster generation and editing in this skill uses Codex's built-in `image_gen` workflow.

- Do not call image-generation CLIs, provider SDKs, or external APIs.
- Do not request an API key.
- If the source image is a local project file and needs editing, first make it visible to Codex's image workflow, then perform a built-in image edit.
- Copy the selected generated result from Codex's generated-image storage into the project before game code references it.
- Prefer PNG for game assets.
- For sprites and UI, request true transparent output. Do not use chroma-key backgrounds or a separate background-removal service unless the user explicitly supplies another workflow.

## 4. Prompt assembly

Build prompts from four parts:

```text
<asset kind and framing> + <asset description> + <STYLE FORMULA verbatim> + <kind-specific constraints>
```

Keep asset descriptions short and stable. Use descriptive roles such as `round blue slime` rather than lore-only names that give the model no visual information.

### Sprite

Use for characters, enemies, items, props, and pickups.

Prompt requirements:

- single subject unless the manifest explicitly needs a group;
- full subject visible, nothing cropped;
- centered with useful transparent margin;
- perspective exactly matching the STYLE FORMULA;
- true transparent background;
- no text, labels, borders, ground plane, or unrelated props;
- readable silhouette at game scale.

Example structure:

```text
Game sprite of <description>, single subject, full body/object visible and centered.
<STYLE FORMULA>
Transparent background. No text, no border, no unrelated objects, no cast shadow outside the silhouette.
```

### Background

Use for full-frame scene art.

Requirements:

- correct gameplay perspective;
- no player character unless explicitly requested;
- no UI or readable text;
- composition leaves the gameplay area readable;
- slightly lower local contrast/detail than foreground actors when the game needs strong silhouettes.

### UI element

Requirements:

- one icon/button/frame element;
- true transparent background where appropriate;
- crisp readable silhouette;
- no baked-in label text unless the user explicitly needs text rendered into the asset;
- visual language consistent with the game but simpler than scene art.

### Tile/texture source

Use the texture-specific workflow in `textures.md`. The prompt should request a square, evenly lit, non-perspective surface with no focal object. The deterministic local pipeline remains responsible for final seam correctness and PBR maps.

### AutoSprite sheet

Use `2d-animation.md`. One sheet contains one action, one view/direction, one character identity, and a strict grid.

## 5. Reference-preserving edits

When editing an existing asset or material reference, write explicit invariants in the image-edit request.

For example:

```text
Change only the left/right and top/bottom continuity needed to make the surface tileable.
Preserve the material identity, palette, lighting, scale, texture density, and all undamaged interior details.
Do not add objects, text, borders, vignette, or directional lighting.
```

For character edits:

```text
Keep the same character identity, costume, body proportions, face, palette, camera angle, scale, and rendering style.
Change only <requested change>.
```

If the edit drifts outside those invariants, retry once with a stronger preservation clause before changing strategy.

## 6. Generation budget

Default to one final candidate per manifest asset. Retry at most twice when there is a concrete failure such as:

- wrong perspective;
- cropped subject;
- missing transparency;
- major style drift;
- incorrect object/content;
- unusable sprite-grid structure.

Do not regenerate the entire asset set to fix one local failure. A full-set regeneration is appropriate only when the user changes the art direction itself.

## 7. Scale and coherence

Record `relative_scale` or equivalent sizing data in game design/config when object proportions matter. The hero can be defined as `1.0`, with doors, enemies, pickups, and hazards measured relative to it.

Before coding many assets into the game, visually inspect a small contact composition at intended relative sizes. Check:

- same rendering style and outline language;
- hero/enemy readable against the environment;
- signal colors reserved for their intended roles;
- perspective consistent across all assets;
- object proportions believable in the same world.

Do not encode relative game scale by asking the image model for arbitrary pixel sizes inside the prompt. Generate clean source art, then size it deterministically in the game or local image processing.

## 8. Pixel-art handling

When the STYLE FORMULA is pixel art:

- request crisp intentional pixel clusters, limited palette, and no anti-aliased painterly edges;
- do not upscale/downscale repeatedly;
- use nearest-neighbor resizing in local processing;
- align final in-game rendering to integer or controlled pixel scales where possible.

For non-pixel art, use a high-quality resampler such as LANCZOS when deterministic resizing is required.

## 9. Verification

A generated asset is not accepted merely because the file exists. Inspect it for:

- content correctness;
- perspective;
- transparency when required;
- crop/margins;
- style consistency;
- readability at intended game size;
- absence of unwanted text/watermarks/borders;
- for animation sheets, identity and alignment across frames;
- for texture sources, material consistency before the local seamless pass.

If a visual defect can be fixed deterministically without changing the art, prefer local processing. If the semantic image content is wrong, regenerate rather than trying to repair it with brittle code.
