# Local Browser Game Assembly and Verification

Read this reference after planning and asset-generation references, but before writing full game code.

This skill produces locally runnable browser-game source. It does not depend on a hosted game platform and does not deploy or publish the game.

## 1. Project layout

Recommended simple layout:

```text
game/
├── index.html
├── game.js
├── strings.js
├── assets/
│   └── ...
└── design/
    └── assets.csv
```

Existing projects keep their current architecture unless there is a concrete reason to change it.

Use relative asset paths such as `./assets/hero.png`. Avoid root-relative paths when the game may later be hosted under a subpath.

## 2. Runtime choice

For a small generated browser game, prefer a plain HTML page with `<canvas>` and an ES-module `game.js`. Do not introduce a framework solely for a game loop.

A framework/library is fine when the existing project already uses it or the requested mechanics materially benefit from it. Pin vendored third-party files or package versions rather than using floating `latest` CDN URLs.

## 3. Input contract

Map every input source onto the same logical command names.

Keyboard uses physical codes:

```js
const KEY_BINDINGS = {
  KeyW: "up",
  KeyS: "down",
  KeyA: "left",
  KeyD: "right",
  Space: "action",
  ArrowUp: "up",
  ArrowDown: "down",
  ArrowLeft: "left",
  ArrowRight: "right",
};
```

Use `event.code`, not `event.key`, so letter controls survive non-Latin keyboard layouts.

If mobile is in scope, core play must work touch-only. If gamepad is declared, poll the Gamepad API and translate buttons/axes into the same command layer.

Local same-screen multiplayer uses separate binding sets/player command streams. Online multiplayer is outside this skill unless the user supplies an existing backend/toolchain.

## 4. Responsive canvas

For canvas games:

- resize on viewport/orientation changes;
- account for `devicePixelRatio` but cap it if needed for the performance budget;
- separate logical game coordinates from CSS/display size;
- pause or safely stop gameplay input when the tab loses focus when appropriate;
- include the mobile viewport meta tag.

Minimal pattern:

```html
<meta name="viewport" content="width=device-width, initial-scale=1">
<canvas id="game"></canvas>
<script type="module" src="./game.js"></script>
```

## 5. Deterministic real-time loop

Real-time game simulation must not depend directly on render frame rate.

Use a fixed timestep:

```js
const STEP = 1000 / 60;
let acc = 0;
let last = performance.now();

function frame(now) {
  requestAnimationFrame(frame);
  acc += Math.min(now - last, 250);
  last = now;

  const commands = readCommands();
  while (acc >= STEP) {
    update(STEP, commands);
    acc -= STEP;
  }
  render(acc / STEP);
}

requestAnimationFrame(frame);
```

When reproducibility matters, use seeded gameplay RNG and keep purely cosmetic randomness separate.

## 6. Asset loading

Consume assets by the role/id in `design/assets.csv` rather than ad-hoc filenames scattered through game logic.

For sprite sheets, keep animation metadata in one data structure:

```js
const ANIM = {
  idle: { src: "./assets/hero_idle.png", frames: 16, cols: 4, rows: 4, fps: 12, loop: true },
  attack: { src: "./assets/hero_attack.png", frames: 12, cols: 4, rows: 3, fps: 14, loop: false },
};
```

Missing required assets are errors. Do not silently replace them with unrelated placeholders.

## 7. Strings and localization

Player-visible strings live in `strings.js` or structured data rather than being scattered through simulation code.

Example:

```js
export const STR = {
  start: "Start",
  restart: "Restart",
  gameOver: "Game Over",
};
```

This keeps later localization a data change rather than a hunt through gameplay code.

## 8. Dev overlay

For real-time games, support a lightweight optional diagnostics overlay such as `?dev=1` showing at least:

- FPS;
- frame time;
- active entity count;
- draw count when the renderer exposes it;
- useful current state for debugging.

The overlay is disabled by default.

## 9. Performance rules

Before claiming a performance problem, measure it.

Prefer:

- batching repeated entities;
- avoiding per-frame allocations in hot loops;
- caching immutable calculations;
- spatial partitioning only when scene scans are measured as a problem;
- not drawing or updating definitely inactive/offscreen content when correctness allows it.

Do not preemptively add complicated pooling/indexing without evidence.

## 10. Local verification

Run from the game root over HTTP:

```bash
python3 -m http.server 8000
```

Do not rely on `file://` because ES modules and browser security behavior differ.

Verify all relevant items:

- launch → meaningful action → win/lose/endless-state behavior → restart;
- no missing asset requests or console errors;
- all manifest rows actually used where intended;
- responsive canvas/layout;
- keyboard-only path;
- non-Latin keyboard layout via `event.code`;
- touch-only path when mobile is declared;
- gamepad-only path when gamepad is declared;
- local multiplayer with all local players when applicable;
- fixed-timestep behavior under rendering slowdown;
- pause/focus handling;
- player-visible strings centralized;
- generated sprite sheets animate in correct row-major order;
- transparent sprites do not show halos/background blocks;
- tile textures visibly repeat without obvious seams.

## 11. Existing-game iteration

When modifying supplied source:

1. inspect the existing architecture first;
2. preserve working build/run conventions;
3. preserve unchanged assets;
4. amend `design/assets.csv` only for changed/new asset roles;
5. regenerate only affected visual assets;
6. verify the same critical path that worked before plus the changed behavior.

Do not rewrite a working project into the default canvas skeleton merely because this reference contains one.

## 12. Packaging

Only create a ZIP when the user requests it or the next toolchain explicitly needs one.

From the project root:

```bash
zip -r /absolute/path/to/game.zip . \
  -x '*.DS_Store' 'node_modules/*' '.git/*'
```

Do not imply the ZIP has been hosted or deployed. This skill's delivery boundary is locally verified source/assets.

## 13. Honest delivery

At delivery, report:

- project/source location;
- how to run locally;
- generated asset files;
- known human-review points such as animation feel or visual cohesion;
- anything that could not be verified in the available environment.

Do not fabricate a public URL or claim external publication.
