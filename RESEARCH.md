# Attribution and display research (r12)

## Rendering diagnostic update

The matching r11 log isolates the current blocker to empty clip rejection.
Original BC1330..BC1364 has a shared-sentinel viewport substitution omitted by
earlier plugin/fragment fixtures. See [R12_RENDER_LOGGING.md](R12_RENDER_LOGGING.md)
for exact indirection and complete native ARM coverage. R11_RENDER_LOGGING.md
retains the earlier telemetry contract; R10_HIGHLIGHTS.md retains shader/texture
research. Visible r12 alignment remains pending.

## Existing traces

Current texture identity research and the confirmed R9 rejection are documented in [R10_HIGHLIGHTS.md](R10_HIGHLIGHTS.md).
R8_HIGHLIGHTS.md records the observation initialization repair.
These are static traces and executable fixtures, not gameplay coverage.
R6 implements rendering for the verified normal-vertex, 2D-shader, full-viewport
and direct/native parallel presentation routes. See [R6_HIGHLIGHTS.md](R6_HIGHLIGHTS.md).
The R5 placement decision below is retained as historical evidence; it no longer
describes the current renderer. Unknown paths remain unmarked.

## Decisions and accepted copies

Selector `0x3822BC` returns normal 22, Horrible Luck 8, Bad Luck 16, Good Luck 25,
Great/Bounty-equivalent Luck 28 or Miraculous Luck 31. Its direct ARM callers are
main count `0x381FEC` and secondary `0x382E1C`. Main count preserves quest
guarantees, RemAddFrameA/B and meal checks 0x10/0x11; it compares threshold >
(randU16 & 31), caps at eight and clamps zero to one. Secondary starts at two and
has six comparisons, the last enabling slot eight. Absent tables generate no items.

Fixtures execute both full native count bodies and selector with deterministic
quest/player/table and RNG-source stubs. Across 1,092 cases, compiled natural mode
matches original counts/consumed rolls; forced mode matches the original cheat.
Native item selection is not rerun. R4 captures actual four-byte item/quantity
entries at the native array-copy boundary; generator returns are diagnostic only.

UI construction `0x3874E0` has these verified eight-entry copies. Fixtures execute
each original fragment with duplicate IDs/distinct quantities and untouched
neighbor sentinels.

| Native return/copy start | End exclusive | Source | Destination |
|---|---|---|---|
| `0x3875BC` | `0x387680` | r7 | `*(ui+0x5C)`, slots 0..7 |
| `0x3878E0` | `0x3879A4` | r7 | `*(ui+0x5C)`, slots 0..7 |
| `0x387B00` | `0x387BC4` | r6 | `*(ui+0x5C)+32`, slots 8..15 |
| `0x388084` | `0x388144` | r5 | `*(ui+0x64)+32`, slots 8..15 |

The first two follow main wrapper `0x381D30`; the third is direct main generation;
the fourth follows secondary `0x382E1C`. Exact caller/destination and all generated
entries must match at UI construction return. Unknown routes publish no attribution.

List copy `0x623C08` copies min(source count, list capacity) by index.
**Items are inline at list+0x60, not behind a pointer.** Flags copy to list+0x120
from the separate r2 descriptor. Thirty-six native count/capacity combinations
verify entries, flags and untouched tails before refresh `0x623C68`. Runtime
follows source-relative offsets into that inline array after contents match;
there is no ID search.

Known category arrays are fields +0x5C/count +0x60, +0x64/count +0x68,
+0x6C/count +0x70 and +0x74/count +0x78. Result update `0x384848` observes
reward states 2..5 at +0x3C; leaving them or destruction invalidates provenance.
This establishes only the listed routes, not every category/display mapping.

## Geometry traced, with limits

List refresh uses group list+0x4C, group records with stride **0x28 (40 bytes)** and node-ID arrays
at +0x16C. Holder lookup `0x546F84` selects a table using holder+0x298, resolves
the group root and accesses node pointers through root+0xD8. Complete array/
category/row-to-node identity, instance/vtable guards and lifetimes need fixtures.

Native world-quad helper `0xA4B390` uses anchors +0xA0, size +0xB4, current matrix
+0x10, direction bit 0x40 at +0x56 and hard-VFP scale s0. Its 216 cases cover nine
anchors, both directions, three centre scales, translation, rotation and shear.
These are **world quads, not verified screen coordinates**. Texture vertex
construction has a different local Y convention, preventing direct ImGui placement.

Texture render `0xA4FC9C` chooses model publisher `0xA4EB9C` or alternate
`0xA3E3B0`. CBGUIMatrix ID 0x2D7 publishes at renderer+0x18BC; GUI global
publisher `0xA397D4` uses CBGUIGlobal 0x2D6 at renderer+0x18B4. The model
includes draw-context depth in Z. MFX reflection for FGUICalcPosition2D lists both
GUI matrices and CBViewProjection 0x16F. Shader variant, matrix order and viewport
Y conversion remain unverified; dependency names do not establish an equation.

Scissor `0xA37C1C` uses draw-context +0xC0/+0xC4 offsets and +0xC8/+0xCC scales,
intersects renderer +0xC4..+0xD0 viewport bounds and publishes +0xE4..+0xF0 clips.
View/projection getters `0x885804`/`0x885824` reach tagged camera renderer+0xD7C.
Binding these to the actual GUI draw and presented framebuffer remains open.

## Local research inputs

Read-only RomFS inputs were copied under ignored `work/please-do-better/inputs/`.
Originals are unchanged. Game binaries, shader programs, decompiled functions and
external emulator snapshots are not committed or bundled.

| Copied input | SHA-256 |
|---|---|
| AppShaderPackage.mfx | `2b80892da570f42b38dfe46b31234503af3d593eb634da10109c37534ac36627` |
| root.arc | `63d861e9beb9464ca8308760479ed2514d87e9975568889b9599e7a22d91615c` |
| sc/NX/root.spkg | `7dea1d84f3e64d1a79df8f7a4d7bdf063643e996de6cfab95e7c5d782f8b795e` |

Root ARC holds one shader resource. Its large size requires the 30-bit field;
independent bounded zlib extraction produced 58,841,740 bytes without altering
the shared 24-bit helper. Native loader `0xCE1FBC` verifies SPK magic, version
0x26 and shader version 0xB2D34C60. Metadata/variant tables were inspected, but the
exact GUI vertex program and constant-buffer bindings remain unresolved. No GPU
equation is accepted from a guessed table entry or unrelated shader variant.

Read-only Ghidra exports retain original bytes/mismatch counts under ignored
work/tmp paths; no GZF or annotations were edited. Saved DTI provides leads,
subordinate to original instructions.

## Required next coverage

- R4 forced count-to-copy observation is now supported by the user's item-grid
  and village screenshots and the installed candidate hash. See R5_OBSERVATIONS.md. R3's
  threshold 31 and zero generation/publication counters justify independent copy
  capture; they do not identify the generator detour's runtime failure cause.
- Resolve the exact GUI shader variant and prove matrix, viewport and framebuffer
  conversion against native bindings.
- Fixture every relevant category copy, list row/group/node route and lifetime
  before accepting that provenance for display.
- Capture geometry at the correct draw boundary, including animation/clipping;
  uncertain and stale samples must remain unmarked.
- Then implement the subtle gold pulse/procedural marker and fixture scaling,
  row changes, cursor/icons, clipping, empty entries and screen close.

The preceding unresolved geometry notes describe the historical R5 gate. R6
implemented the renderer with static proofs; its first user-run grid failed to
draw. R7 repairs the binding/copy defects; gameplay alignment remains pending.

## Historical R5 placement trace and acceptance decision

State-1 UI routine `0x384AF0` can grow the main array to 16 or 48 entries before
opening the grid. Original copy loops `0x384BF0..0x384C24` and
`0x384C7C..0x384CB0` preserve item/quantity pairs at the same indices. The old
allocation is freed before UI+0x5C is replaced. R5 snapshots it on entry to the
existing paired update, verifies the copied prefix on return and publishes
old/new array identities with the batch serial. Tail entries create no provenance.
This repairs a missing route; matching item IDs alone would not repair it safely.

The full original `0x623C08` refresh uses the group multiplied by `0x28`, the root
identifier at list+group*0x28+0x160 and item-node ID table at +0x16C. Item assignment
`0x56E62C` obtains item icon information and calls holder `0x546F84`; visibility
`0x56E530` calls `0x545630`. Holder lookup resolves the root/node tables. This
traces **item-icon nodes**, not a verified slot-frame perimeter. No assumption
that neighboring node IDs identify the background frame is accepted.

Texture draw `0xA4FC9C` joins `0xA4FE50` only after its selected vertex constructor
reports success. The displaced words are `LDR r0,[r6]` and `AND r0,r0,#15`, without
flag writes. R5 compiles a fixed, fully preserving gateway for this boundary and
checks its signature, but **does not install it**. It captures no geometry.
Separate transaction fixtures show optional-site rejection/rollback does not
touch working conditional or observation hooks and allocates no second arena.
Successful instruction replay is not acceptance of the rendering path.

The GUI global/model publishers and scissor were exported read-only from Ghidra
and compared against the pinned original image, with zero byte mismatches.
The model publisher copies node+0x10's matrix and adds draw-context depth to Z;
the alternate copies it unchanged. The global publisher copies 16 words.
Scissor applies context offsets/scales and intersects viewport bounds. The SPK
loader `0xCE1FBC` verifies format 0x26 and separates relative metadata from GPU
code: copied root.spkg's 0xDF20C metadata/file boundary plus 0x373E880 GPU bytes
equal the 58,841,740-byte file. That parse does not identify the active vertex
program or prove FGUICalcPosition2D's multiplication/Y/viewport conversion.

Forge calls free-render inside `customQueuePresentTexture`, submits ImGui to
that queue/texture index, then calls the native present. Its installed graphics
API exports initialization/menu status, not the queue/window/texture index or a
matching native GUI draw epoch. Reading an uncorrelated latest draw snapshot
would not prove it belongs to that presented image, especially across threads.
The maintained Forge baseline is left unchanged.

The acceptance gate remains closed for three concrete missing proofs:

1. Category/row/index to the actual slot-frame node, including lifetime guards.
2. Selected GUI vertex shader, matrix order, viewport/Y conversion and clipping
   to the framebuffer used by Forge's ImGui draw list.
3. Native draw epoch/target correspondence with Forge's presented texture.

No screen coordinates, 64-entry binding/geometry publication system or gold
renderer is accepted or implemented. The planned warm gold, 1.5px-at-720p border,
two-second pulse and upper-left procedural sparkle remain pending these proofs.
Scaling/animation/cursor/geometry fixtures cannot honestly pass before them.

Reproduce the native receipts without changing the imported database:

```bash
python3 scripts/please_do_better_research.py export
python3 scripts/please_do_better_research.py check
tools/mwc-analysis-venv/bin/python scripts/please_do_better_display_probe.py
```

The export uses `-readOnly -noanalysis` and the shared Ghidra export helper.
Its original bytes are checked against the pinned main; shader input hashes and
SPK bounds are checked too. Receipts are saved in ignored research/build paths.
The compiled fixture also executes the original group address calculation,
holder node lookup and complete CPU scissor helper. These synthetic tables and
clips establish local CPU behavior, not the missing frame/shader correspondence.
