# R9 presented-target guard and draw diagnostics

The user-supplied R8 item-grid screenshot shows eight generated rewards, one
extra, one bound extra, zero highlights, zero capture/mapping faults and an
unsupported draw. The installed NRO matches the immutable R8 candidate:
`f6b6e2acbbc4333d8b422a5d72282d01b89f87bc477896299eb24dac01f8acab`.
The latest Eden master-10bcd2d849 log reports successful R8 conditional,
observation and highlight publication. This supports the R8 initialization
repair on this reported grid. It does not establish visible highlights.
Screenshot/log copies and preservation hashes are in ignored
`work/please-do-better/r9-report/`.

## Verified changes

Original `main+0xBC0E98` resolves the default surface sentinel obtained through
`sRender+0x389C0 -> +0x204 -> first surface` to the actual presentation surface
through `sRender+0x389CC -> +0x204 -> first surface`. A packet already naming
that actual surface follows the same native submission path. R8 required the
sentinel alone and incorrectly suppressed the resolved form. R9 accepts either
nonzero identity. Unrelated offscreen surfaces and offset/reduced viewports remain
rejected; clipping, shaders, exact slot identity, producer/presentation serials
and immutable snapshots remain checked. No additional hook or arena is needed.

Original `0xBC0E98` also uses target flag `0x200` to select viewport `+0x28`
and clip `+0x48`, in place of `+0x18` and `+0x38`. R8 rejected the flag itself.
R9 reads the selected immutable packet rectangles, clamps the viewport to the
packed surface extent at `+0x58`, and intersects the clip. Only a full, nonzero,
zero-origin effective viewport is accepted. Actual reduced/offset rectangles
remain unmarked. The original ARM rectangle selection/clamp/scissor fragments
pass 80 fixture checks independently of the plugin implementation. Full normal
and alternate-bank fixtures both draw; an inactive clip bank cannot affect the
selected path. The same presented-frame and framebuffer-size checks still apply.

R8's generic unsupported-path counter does not identify which check rejected
the user's frame. The resolved-target defect is verified in original code and
compiled regression fixtures; its involvement in this particular screenshot
is still unconfirmed. R9 records the precise rejection class and bounded
actual target identities or shader bindings, and selected viewport values for viewport failures. Closed diagnostics display that
reason. The Eden log receives at most one entry per rejection class per process,
with nine bounded binding values. Logging is deferred to Forge free-render; the
geometry gateway calls no external formatter/logger while GE is live. The snapshot
cannot affect game results.
Historical rejection details are explicitly labeled "Last suppressed draw";
they do not claim the current frame is unsupported.

The normal slot resources all specify Tiling=0. The alternate constructor
`0xA50290` is tiled indexed geometry, not the normal four-vertex strip. It remains
unsupported. The normal constructor submits a draw, then runs `0x882760`, which
can submit additional effects; it does not pop or restore the entire renderer.
The gateway remains after successful construction/submission at `0xA4FE50`.

Original runtime program construction `0xBD8F8C` calls reflection merge
`0xBD9478`. That merge appends unique constant IDs, texture and sampler IDs,
vertex shader before pixel shader. Offline reflection of all thirteen examined
programs produces exactly the existing serialized whitelist sequences. Twelve
have the verified XY/W=1 transform; the perspective blend variant stays rejected.
The resource, reflected sequence and original instruction receipts are checked
by `scripts/please_do_better_highlight_research.py check`.

## Remaining runtime evidence

R9 has not been installed or run. A separately authorized user test must confirm
visible borders/sparkles on a populated grid. If still suppressed, the precise
reason and bounded values in Diagnostics/the Eden log identify the blocked gate.
No guessed coordinates, arbitrary shader acceptance or offscreen projection
fallback is added. Natural positive luck/no luck, repeated screens, collection,
mode toggles, cursor/animation alignment, village return, multicore/translation
freshness and Ryujinx remain in MANUAL_TESTS.md.

All 85 recorded R1-R8 candidate files, installed packages and maintained Forge
are preserved. DEVELOPMENT continues. No installation, activation, launch,
save/settings edit, push or publication. See R8_HIGHLIGHTS.md for observation
initialization and R6_HIGHLIGHTS.md for the geometry/presentation contract.

## Reproduction

With the preserved pinned research project and copied shader/resource inputs:

```bash
python3 scripts/please_do_better_highlight_research.py prepare
python3 scripts/please_do_better.py build
python3 scripts/please_do_better.py verify
python3 scripts/mod_distribution.py check
```

The prepare command regenerates all six read-only native trace groups, including
program construction/reflection. It preserves Ghidra annotations and compares
every receipt instruction to the original copied main. Build does not launch a
game or GPU. The candidate remains local DEVELOPMENT.
