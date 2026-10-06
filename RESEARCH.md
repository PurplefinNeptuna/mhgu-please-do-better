# R2 attribution and display research gate

These are static traces and executable fixtures, not gameplay coverage.
The required highlight gate is **INCOMPLETE**. No border renderer is accepted.

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
Native item selection is not rerun. Generation observation snapshots actual
four-byte item/quantity entries afterward.

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

List refresh uses group list+0x4C, group records with stride 28 and node-ID arrays
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

- Resolve the exact GUI shader variant and prove matrix, viewport and framebuffer
  conversion against native bindings.
- Fixture every relevant category copy, list row/group/node route and lifetime
  before accepting that provenance for display.
- Capture geometry at the correct draw boundary, including animation/clipping;
  uncertain and stale samples must remain unmarked.
- Then implement the subtle gold pulse/procedural marker and fixture scaling,
  row changes, cursor/icons, clipping, empty entries and screen close.

Free-render currently polls preferences and draws nothing. Screen placement,
border rendering and cursor coverage are not reported as passing.
