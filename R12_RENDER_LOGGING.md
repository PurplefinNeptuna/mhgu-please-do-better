# R12 native clipping correction

The user-run r11 reward grid shows sixteen generated slots, ten luck extras,
ten bound slots and zero highlights, with no capture/mapping faults. The latest
Eden master-10bcd2d849 log identifies MHGU 1.4.0 and Forge
1.4.1-originalbi1. Installed r11 matches the accepted candidate NRO:
`60ef558e5df153e4321edbc6cafcd076be83968ddeae680be1e4ed7bf5904b09`.
All three startup groups applied without unsafe words or cache failures.

Across 22 trace bundles, 16,657 exact-node captures matched: four stopped at
item validation and 16,653 reached the clip rejection. None published geometry.
Presentation and free-render callbacks ran. This establishes the clipping check
as the observed immediate blocker, not the contents of its unlogged rectangle.
Copies of the log, screenshot and 118 preserved candidate hashes are under
`work/please-do-better/r12-report/`.

## Native rule and fix

Original `main+0xBC12D8..0xBC1364` selects the rectangle bank using flag `0x200`,
intersects it with the clamped viewport and normalizes each inverted axis to
zero. It then compares all four resulting edges with a shared sentinel. On an
exact match, it substitutes the cached viewport. Earlier plugin fixtures stopped
before this equality/substitution tail, so an empty default scissor was wrongly
rejected by the plugin even when native rendering would use the full viewport.

`BC12F8` loads the literal at `BC13D8`; `BC1314` loads from `PC+8+literal`, giving
main-relative GOT entry `0x183F2B0`. The pinned offline word there is `0x191EAA0`
(in BSS). R12 reads the relocated runtime pointer and its four signed edges with
mapping checks. It never assumes the sentinel currently contains zero. The
original-byte receipt checks the indirection, and ARM execution fixtures exercise
both banks, zero and nonzero sentinels, partial/empty/inverted/outside rectangles.

R12 reproduces that complete rule. A nonmatching empty clip stays suppressed;
a missing/unreadable sentinel also stays suppressed. Exact provenance, shader,
full-viewport, presentation-image/frame and stale-epoch guards remain. Forcing,
settings, attribution and RNG are unchanged. No new hook, arena, TLS slot or heap
allocation is introduced; maintained Forge is unchanged.

## Emulator-log evidence

Bounded r11 telemetry continues with an r12 prefix. New `clip input` and
`clip effective` records include selected flags, clamped viewport, raw scissor,
runtime sentinel pointer/edges, read validity and effective edges. Formatting
runs only in Forge callbacks. Gateways publish fixed atomic snapshots.
All 22 formats are checked against Forge's 520-byte buffer. Per-screen limits
remain eight initial bundles then every 120 callbacks, at most 24 bundles;
per-process cap is 128. ImGui stays compact. See R11_RENDER_LOGGING.md for the
remaining stage-label definitions.

## Remaining coverage

The native clipping omission is corrected and covered offline. The exact raw
rectangle in the supplied r11 run was not logged, and r12 has not been run.
Visible gold borders/sparkles, cursor/animation alignment, natural positive luck,
no luck, live toggles, repeated grids, collection/return, restart persistence,
Eden multicore/translation freshness and Ryujinx compatibility remain pending.
No installation, activation, launch, existing save/settings edits, push or
publication is included. DEVELOPMENT status remains.
