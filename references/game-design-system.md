# Game Creation System

This reference is the design and engineering core for a game-generation run. Read it first for a full game, before image generation and before game code.

## Operating model

A full run has three ordered stages:

1. **PLAN** — resolve the game profile, core loop, controls, budgets, asset manifest, and STYLE FORMULA.
2. **BUILD** — generate independent assets, post-process them locally, and write the game while preserving the plan's numbers and interfaces.
3. **VERIFY** — run the complete loop locally, measure behavior, fix causes rather than symptoms, and deliver source/project files.

Do not write game code or generate final art before PLAN closes. The mandatory written planning artifact is `design/assets.csv`; the STYLE FORMULA may be recorded beside it or in the project notes if useful.

## 1. Game profile

Resolve every axis that materially affects implementation:

| Axis | Typical choices |
|---|---|
| Time | real-time / turn-based / pause-at-will / no time |
| Space | continuous 2D / discrete grid / abstract |
| Agency | one hero / squad / cursor-hand / system manager |
| Conflict | vs system / local players / self / none |
| Content | authored / procedural / emergent / player-created |
| Outcome | win-lose / endless / player-set goals |
| Players | solo / local co-op / local versus |
| Session | minutes / hours / persistent accumulation |
| Engagement | execution / calculation / discovery / expression / story / social / accumulation |

Pick one or two primary engagement sources. Rewards, difficulty, and progression should reinforce them.

### Delivery context

Fix the target input and display contexts before code. For browser games, default to desktop + mobile unless the brief narrows it. If gamepad support is declared, every core verb must be reachable through it. Keyboard bindings use physical key codes (`event.code`), not typed letters. No hover-only interaction when touch is supported.

Performance budgets target the weakest declared device.

## 2. Experience formula

Write one sentence without genre labels:

> The player feels ___ because the game constantly ___.

Use this to arbitrate mechanics, content, presentation, and scope.

Then align four pillars:

- **Mechanics** — what the player repeatedly does.
- **Aesthetics** — what the game communicates visually and through motion.
- **Story/context** — even abstract games have tension and progression.
- **Technology** — what the browser/runtime can reliably support.

A pillar that supports nothing else is scope ballast.

## 3. Formal elements

Decide or explicitly omit players, goals, actions/verbs, rules, resources, conflict/resistance, boundaries, and outcome/restart behavior. The first meaningful action should happen quickly after launch.

## 4. Interaction laws

Every core action needs both an immediate visible response and a later consequence in the game state. If an action has neither, remove it. If it has only delayed consequences, improve acknowledgement.

Teach one new pattern at a time: introduce safely, test with a mild cost, combine with known patterns, then examine under pressure. Do not confuse content volume with depth.

Keep outcomes undecided at the horizons that matter. Choose a few actual uncertainty sources such as execution, hidden information, anticipation, resource tradeoffs, or another player's choices.

## 5. Verbs, loops, and information

Few strong verbs beat many weak ones. A strong verb interacts differently with multiple object types or contexts.

For every feedback loop, decide whether it is positive or negative. Positive loops can make an early lead decide the game too soon; negative loops can erase the reward for skill. A losing player should usually have a believable recovery path without making good play irrelevant.

Map visibility deliberately. Hidden information that affects outcomes needs a discoverable trail; otherwise it feels arbitrary.

## 6. Full walkthrough checklist

Resolve these before mass content production:

1. **Representation** — camera/layout never hides information required for the current decision.
2. **Input** — frequent actions use cheap gestures; conflicting inputs resolve predictably.
3. **Agency metrics** — movement speed, jump length, move range, visible option count, or equivalent numbers are frozen before building lots of content.
4. **Resistance × verb matrix** — every obstacle has at least one understandable answer; no single verb answers everything.
5. **Peaks** — periods end in a combined test of recently learned patterns.
6. **Rewards** — feed the declared engagement source; major rewards sit on interest-curve peaks.
7. **Interface** — each visible element supports a player decision or is hidden until needed.
8. **Economy** — every resource has sources and sinks.
9. **Mechanic delivery** — introduce one pattern at a time.
10. **Return experience** — returning players can immediately see the current goal and next step when the game has persistence.

## 7. Code architecture

Optimize architecture for cost of change, not abstract purity.

Use these patterns when the symptom requires them:

- behavior depends on frame rate → fixed timestep, separate render interpolation;
- many capability combinations → composition/components rather than subclass explosion;
- replay/undo/multiple input sources → command objects;
- boolean-flag forests → explicit state machines;
- gameplay directly pokes UI/audio → events/subscriptions;
- measured allocation pressure → pooling/dirty flags/spatial indices.

Logic and rendering stay separable enough to test. Persistent state gets a clear serialization format early.

## 8. Performance law

Performance is a design budget, not cleanup work. For real-time browser games, target stable frame pacing on the weakest device; avoid per-frame object churn; batch large swarms of identical entities; do not create or draw definitely invisible objects; and keep a dev overlay for FPS, frame time, entity count, and draw count where available.

Diagnose in order: draw-call pressure → GPU-bound work → CPU simulation → allocation/GC spikes.

## 9. Content construction

Calibrate content against frozen agency metrics. Every required gap, cost, route, timer, and threshold must be achievable by the actual player capabilities and economy.

Alternate compression and expansion: pressure/fewer options versus safety/overview/planning. Monotony in either direction is a defect.

## 10. Response and feel

Every action gets immediate acknowledgement. Significant actions should later echo in the world or state. Keep polish numbers such as shake, hit pause, easing, acceleration, and tolerance windows in data/config so they can be tuned one change at a time.

## 11. Balance

Place comparable options on a shared cost/value curve. Tune expected value and variance separately. Progression should slow smoothly rather than hit arbitrary walls. Inflation is usually fixed by meaningful sinks, not by repeatedly increasing prices.

## 12. Player cognition and accessibility

Critical signals use more than color alone. Do not show instructional text during peak load. Make failures explain why an action was rejected and, when appropriate, how to make it valid.

All player-visible strings should be centralized. Declared controls should be cleanly data-driven. Accessibility switches such as shake/flash reduction and readable text scale belong in the design when the game uses those effects.

## 13. Determinism and debugging

For real-time simulation, prefer fixed timestep and seeded gameplay randomness where reproducibility matters. Keep cosmetic randomness separate.

Debug in this order: reproduce stably → state a hypothesis → observe state/logs → narrow the cause space → fix the cause → leave a guard/assertion/test where practical. During tuning, change one meaningful variable at a time.

## 14. Honest limits

AI-generated visuals still need visual inspection. A syntactically valid spritesheet can contain identity drift, impossible poses, uneven perspective, or poor silhouette readability. A mechanically complete game can still be unfun. Surface the remaining human-review points at delivery rather than overclaiming certainty.
