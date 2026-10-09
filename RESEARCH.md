# Please do Better native research

Current overlay/state rules are in [IMPLEMENTATION.md](IMPLEMENTATION.md).
The accepted R14 Forge background overlay replaced the experimental native
texture-transfer route. The R13 user log showed valid slot geometry and zero
execution of both downsample hooks. Historical R5-R13 pending-gate notes remain
in Git; they do not describe the current renderer. Gameplay acceptance and
remaining coverage are in [RUNTIME.md](RUNTIME.md) and [MANUAL_TESTS.md](MANUAL_TESTS.md).

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


## Native geometry bindings

List refresh uses group records of stride `0x28`, root ID at
`list+group*0x28+0x160` and node-ID arrays at `+0x16C`. Holder lookup `0x546F84`
selects holder+0x298's table, resolves the root and accesses root+0xD8 node pointers.
Item assignment `0x56E62C` and visibility `0x56E530` trace item-icon nodes; nearby
IDs alone do not identify frame perimeters.

World-quad helper `0xA4B390` uses anchors +0xA0, size +0xB4, matrix +0x10,
direction bit 0x40 at +0x56 and hard-VFP scale s0. Its 216 original-execution
cases covered nine anchors, two directions, three centre scales, translation,
rotation and shear. World quads alone do not establish framebuffer coordinates.

Texture draw `0xA4FC9C` joins `0xA4FE50` after successful vertex construction.
The displaced LDR r0,[r6] / AND r0,r0,#15 pair writes no flags. GUI publishers
`0xA4EB9C` and `0xA3E3B0` provide model matrices; `0xA397D4` provides globals.
CBGUIMatrix 0x2D7 and CBGUIGlobal 0x2D6 bind at renderer+0x18BC/+0x18B4.
Scissor `0xA37C1C` applies draw-context offsets/scales and viewport intersections.
R12 also reproduces the native sentinel rectangle fallback at `0xBC12D8..0xBC1364`.
Current shader/full-viewport, clip and exact frame/slot identity guards are
documented with the rendering hooks in the implementation audit.

State-1 `0x384AF0` can grow the main reward array to 16 or 48 entries before
opening the grid. Copy loops `0x384BF0..0x384C24` and `0x384C7C..0x384CB0` preserve
indices, then free the old allocation. Capture snapshots the old prefix before
native return and validates the new pointer/capacity/prefix; it never rereads
freed storage or matches solely by item ID.

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


## Reproduce

```bash
python3 scripts/please_do_better_research.py export
python3 scripts/please_do_better_research.py check
tools/mwc-analysis-venv/bin/python scripts/please_do_better_display_probe.py
```

Export uses `-readOnly -noanalysis` and the shared Ghidra helper. Original bytes,
shader input hashes and SPK bounds are checked; GZF/annotations are preserved.
CPU fixtures do not establish GPU alignment, translation freshness or broader
reward-category coverage.
