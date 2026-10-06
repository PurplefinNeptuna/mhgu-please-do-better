# R4 reward observations

R4 is a local DEVELOPMENT candidate prepared 2026-10-07. Highlights remain
unimplemented until added rewards can be observed in gameplay and the display
mapping passes its separate research gate.

## R3 runtime evidence

The user confirmed the supplied R3 screenshot was taken on the item reward grid.
It reported two reward checks, both forced, two main counts, seven comparison
taps, threshold 31, one reward build entered/returned, zero generation returns,
zero published reward records, zero dropped observations and last UI state 18.
The installed NRO hash matched r3. The latest Eden log identifies master
`10bcd2d849`, MHGU 1.4.0, Forge 1.4.1-originalbi1, and both r3 startup groups
applied with no unsafe words. The screenshot and log are retained in ignored
`work/please-do-better/r4-report/`.

These counters establish that the forcing and comparison gateways executed.
They do not establish which item slots were added. R3's zero extra count was
unavailable observation, not evidence of no luck effect. The reason the generator
detour did not record a return remains unresolved; successful cache calls still
do not establish Eden translation freshness.

## Capture at verified native copies

Five new fixed gateways supplement the existing observations. They allocate no
extra trampoline arena or TLS slot. Their complete signatures are checked against
the pinned offline main and at startup, using the existing owned-word transaction.

| Main offset | Displaced instructions | Observation |
|---|---|---|
| `0x3820B4` | MOV r5,r0; CMP r4,#7 | Actual selected threshold and guaranteed main slot count before the loop |
| `0x3875BC` | LDR r0,[r4,#0x5C]; LDRH r1,[r7] | Main A temporary to UI+0x5C, indices 0..7 |
| `0x3878E0` | Same as above | Alternate Main A copy, indices 0..7 |
| `0x387B00` | LDR r0,[r4,#0x5C]; LDRH r1,[r6] | Main B temporary to UI+0x5C, indices 8..15 |
| `0x388084` | LDR r0,[r4,#0x64]; LDRH r1,[r5] | Secondary temporary to UI+0x64, indices 8..15 |

Main count returns bind only to caller `0x381DC4` with category 0 or caller
`0x387A98` with category 1 inside the exact UI build scope. The secondary builder
returns void; its slot count comes from the six comparison taps, never its return
register. Its scope must return to `0x388084`. Unknown routes are incomplete.

Capture snapshots all eight native source entries before the temporary is freed.
A nonempty prefix must have valid item/quantity pairs, its length must match the
count, and the remaining entries must be empty. Empty tables may yield eight
empty entries. At UI build return, the complete destination copy must match the
snapshot. Duplicate items retain their exact array and slot identities.

The main initial-count tap and comparisons must form a consecutive sequence
ending in a stop or cap eight. Secondary comparisons must start at slot two.
Missing comparisons, unknown thresholds, gaps, extra comparisons after a stop,
bad prefixes or changed copies suppress complete attribution. No RNG is consumed,
generation repeated or item selection changed. The old generator observation
remains a diagnostic counter; publication no longer depends on its return.

## Player-facing evidence

The row retains the last completed batch's threshold, verified generated slots,
and extra slots compared with normal threshold 22. A complete zero-bonus batch
is distinguishable from missing or partial observation. Partial coverage reports
the extra total unavailable. No verified records means the generated count is
also unavailable.

Completed totals remain after collection, screen close or UI state changes.
They describe generation; they do not track collection. Live array provenance
still clears under the previous state guard. State 18 is reported without assuming
it is a verified drawing state. No render code, border, marker or screen coordinate
is accepted. Mode latching, saved preferences and the two conditional sites retain
their existing behavior.

R4 requires a separately authorized installation and gameplay session. Check
copy tap counts, published records, complete coverage, observed tier and extra
slots on repeated comparable quests with force on and off. Capture the exact
candidate/launch set and latest log. See MANUAL_TESTS.md. Local fixtures cannot
confirm Eden multicore/cache behavior, runtime copy coverage or reward effects.
